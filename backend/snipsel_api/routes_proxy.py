from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from urllib import request as urllib_request
from urllib import parse as urllib_parse
from urllib.error import URLError, HTTPError

import requests
from flask import Blueprint, request
from snipsel_api.auth_session import json_response, require_auth
from snipsel_api.errors import api_error
from functools import lru_cache

proxy_bp = Blueprint("proxy", __name__)


# Cache metadata for 1 hour (using a simple lru_cache for in-process memory)
# Note: In a multi-worker production environment, Redis or similar would be better.
@lru_cache(maxsize=1000)
def _fetch_deezer_metadata(url: str) -> dict:
    req = urllib_request.Request(url, headers={"User-Agent": "Snipsel/1.0"})
    with urllib_request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


@lru_cache(maxsize=1000)
def _resolve_deezer_url(short_url: str) -> str:
    req = urllib_request.Request(short_url, headers={"User-Agent": "Snipsel/1.0"})
    with urllib_request.urlopen(req, timeout=10) as response:
        return response.geturl()


@lru_cache(maxsize=1000)
def _fetch_youtube_metadata(oembed_url: str) -> dict:
    req = urllib_request.Request(oembed_url, headers={"User-Agent": "Snipsel/1.0"})
    with urllib_request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


DEEZER_API_BASE = "https://api.deezer.com"


@proxy_bp.route("/deezer", methods=["GET"])
@require_auth
def proxy_deezer():
    """Proxy requests to Deezer API to avoid CORS issues."""
    media_type = request.args.get("type")  # track, album, artist
    media_id = request.args.get("id")
    short_url = request.args.get("url")

    if short_url:
        # Resolve short link (e.g. link.deezer.com)
        try:
            resolved_url = _resolve_deezer_url(short_url)
            # URL structure: https://www.deezer.com/{locale}/{type}/{id} or https://www.deezer.com/{type}/{id}
            parts = resolved_url.split("/")
            # Filter out empty strings from trailing slashes or multiple slashes
            parts = [p for p in parts if p]

            # Look for track/album/artist
            for i, part in enumerate(parts):
                if part in ["track", "album", "artist"] and i + 1 < len(parts):
                    media_type = part
                    media_id = parts[i + 1].split("?")[0]  # strip query params
                    break
        except Exception as e:
            raise api_error(
                502, "external_error", f"Failed to resolve Deezer link: {str(e)}"
            )

    if not media_type or not media_id:
        raise api_error(
            400, "invalid_input", "type and id (or a valid url) are required"
        )

    if media_type not in ["track", "album", "artist"]:
        raise api_error(400, "invalid_input", "invalid media type")

    url = f"{DEEZER_API_BASE}/{media_type}/{media_id}"

    try:
        data = _fetch_deezer_metadata(url)
        if "error" in data:
            return json_response(data, status=400)
        return json_response(data)
    except HTTPError as e:
        return json_response({"error": str(e)}, status=e.code)
    except URLError as e:
        raise api_error(
            502, "external_error", f"Failed to connect to YouTube: {str(e)}"
        )
    except Exception as e:
        raise api_error(500, "internal_error", str(e))


# ---------------------------------------------------------------------------
# Generic link metadata (title + favicon)
# ---------------------------------------------------------------------------


def _extract_coords_from_url(url: str) -> dict | None:
    """Extract coordinates from a URL (Google Maps or Apple Maps)."""
    # Google Maps @lat,lng format
    at_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url)
    if at_match:
        return {"lat": float(at_match.group(1)), "lng": float(at_match.group(2))}

    # Google Maps search/lat,+lng format (from short links)
    search_match = re.search(r"/search/(-?\d+\.\d+),\+(-?\d+\.\d+)", url)
    if search_match:
        return {
            "lat": float(search_match.group(1)),
            "lng": float(search_match.group(2)),
        }

    # Google Maps ?q=lat,lng or ?q=lat%2Clng
    q_match = re.search(r"[?&]q=(-?\d+\.\d+)[,%2C](-?\d+\.\d+)", url)
    if q_match:
        return {"lat": float(q_match.group(1)), "lng": float(q_match.group(2))}

    # Apple Maps ?ll=lat,lng
    ll_match = re.search(r"[?&]ll=(-?\d+\.\d+),(-?\d+\.\d+)", url)
    if ll_match:
        return {"lat": float(ll_match.group(1)), "lng": float(ll_match.group(2))}

    # Apple Maps ?q=lat,lng
    apple_q_match = re.search(r"[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)", url)
    if apple_q_match:
        return {
            "lat": float(apple_q_match.group(1)),
            "lng": float(apple_q_match.group(2)),
        }

    # Apple Maps coordinate=lat,lng (from short links)
    apple_coord_match = re.search(r"[?&]coordinate=(-?\d+\.\d+),(-?\d+\.\d+)", url)
    if apple_coord_match:
        return {
            "lat": float(apple_coord_match.group(1)),
            "lng": float(apple_coord_match.group(2)),
        }

    # Apple Maps center=lat,lng (iframe embeds)
    apple_center_match = re.search(r"[?&]center=(-?\d+\.\d+),(-?\d+\.\d+)", url)
    if apple_center_match:
        return {
            "lat": float(apple_center_match.group(1)),
            "lng": float(apple_center_match.group(2)),
        }

    return None


@lru_cache(maxsize=1000)
def _resolve_map_url(url: str) -> dict:
    """Resolve a map URL (including short links) and extract coordinates.

    Returns a dict with:
    - resolved_url: the final URL after redirects
    - coords: {lat, lng} or None if not found
    """
    parsed = urllib_parse.urlparse(url)
    domain = parsed.netloc.lower()

    result = {"resolved_url": url, "coords": None}

    is_short_link = (
        "maps.app.goo.gl" in domain
        or ("goo.gl" in domain and "maps" in url)
        or ("maps.apple.com" in domain and "/p/" in url)
        or ("maps.apple" in domain and "/p/" in url)
    )

    if is_short_link:
        try:
            resp = requests.head(
                url,
                allow_redirects=True,
                timeout=10,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
            )
            result["resolved_url"] = resp.url
        except Exception:
            pass

    target_url = result["resolved_url"]
    coords = _extract_coords_from_url(target_url)
    if coords:
        result["coords"] = coords
    else:
        coords = _extract_coords_from_url(url)
        if coords:
            result["coords"] = coords

    return result


class _LinkMetadataParser(HTMLParser):
    """Lightweight HTML parser that extracts <title> and favicon <link> tags."""

    def __init__(self) -> None:
        super().__init__()
        self.title: str | None = None
        self.favicon_href: str | None = None
        self._in_title = False
        self._title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self._in_title = True
            self._title_parts = []
        elif tag == "link":
            attr_dict = {k.lower(): v for k, v in attrs}
            rel = (attr_dict.get("rel") or "").lower()
            href = attr_dict.get("href")
            if href and ("icon" in rel) and self.favicon_href is None:
                self.favicon_href = href

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self._in_title:
            self._in_title = False
            self.title = "".join(self._title_parts).strip()


@lru_cache(maxsize=1000)
def _fetch_link_metadata(url: str) -> dict:
    """Fetch a URL and extract title + favicon. Returns a dict with title, favicon_url, domain."""
    parsed = urllib_parse.urlparse(url)
    domain = parsed.netloc or parsed.hostname or url
    if domain.startswith("www."):
        domain = domain[4:]

    fallback = {"title": domain, "favicon_url": None, "domain": domain}

    try:
        req = urllib_request.Request(
            url,
            headers={
                "User-Agent": "Snipsel/1.0 (Link Preview)",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
            },
        )
        with urllib_request.urlopen(req, timeout=10) as response:
            # Only read first 64KB to avoid downloading huge pages
            raw = response.read(65536)
            # Detect encoding from Content-Type header or default to utf-8
            content_type = response.headers.get("Content-Type", "")
            charset_match = re.search(r"charset=([^\s;]+)", content_type, re.IGNORECASE)
            encoding = charset_match.group(1) if charset_match else "utf-8"
            try:
                html_text = raw.decode(encoding, errors="replace")
            except (LookupError, UnicodeDecodeError):
                html_text = raw.decode("utf-8", errors="replace")

        parser = _LinkMetadataParser()
        parser.feed(html_text)

        title = parser.title or domain
        favicon_href = parser.favicon_href

        # Resolve relative favicon URL
        favicon_url: str | None = None
        if favicon_href:
            favicon_url = urllib_parse.urljoin(url, favicon_href)
        else:
            # Fallback: Google favicon service
            favicon_url = f"https://www.google.com/s2/favicons?domain={urllib_parse.quote(domain)}&sz=64"

        return {"title": title, "favicon_url": favicon_url, "domain": domain}
    except Exception:
        # Graceful degradation: still use Google favicon service
        fallback["favicon_url"] = (
            f"https://www.google.com/s2/favicons?domain={urllib_parse.quote(domain)}&sz=64"
        )
        return fallback


@proxy_bp.route("/link-metadata", methods=["GET"])
@require_auth
def proxy_link_metadata():
    """Fetch title, favicon, and optionally coordinates for a URL."""
    url = request.args.get("url")
    if not url:
        raise api_error(400, "invalid_input", "url is required")

    parsed = urllib_parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise api_error(400, "invalid_input", "Only http/https URLs are supported")

    domain = parsed.netloc.lower()
    is_map_url = (
        "google.com" in domain
        and "maps" in url
        or "maps.google" in domain
        or "maps.app.goo.gl" in domain
        or "maps.apple" in domain
        or "apple.com" in domain
        and "maps" in url
    )

    result = {}

    if is_map_url:
        try:
            map_data = _resolve_map_url(url)
            if map_data.get("coords"):
                result["lat"] = map_data["coords"]["lat"]
                result["lng"] = map_data["coords"]["lng"]
            result["resolved_url"] = map_data.get("resolved_url", url)
        except Exception:
            pass

    try:
        metadata = _fetch_link_metadata(url)
        result["title"] = metadata.get("title", domain)
        result["favicon_url"] = metadata.get("favicon_url")
        result["domain"] = metadata.get("domain", domain)
    except HTTPError as e:
        if not result.get("lat"):
            return json_response({"error": str(e)}, status=e.code)
        result["title"] = result.get("title", domain)
        result["favicon_url"] = (
            f"https://www.google.com/s2/favicons?domain={urllib_parse.quote(domain)}&sz=64"
        )
        result["domain"] = domain
    except URLError as e:
        if not result.get("lat"):
            raise api_error(502, "external_error", f"Failed to fetch URL: {str(e)}")
        result["title"] = result.get("title", domain)
        result["favicon_url"] = (
            f"https://www.google.com/s2/favicons?domain={urllib_parse.quote(domain)}&sz=64"
        )
        result["domain"] = domain
    except Exception as e:
        if not result.get("lat"):
            raise api_error(500, "internal_error", str(e))
        result["title"] = result.get("title", domain)
        result["favicon_url"] = (
            f"https://www.google.com/s2/favicons?domain={urllib_parse.quote(domain)}&sz=64"
        )
        result["domain"] = domain

    return json_response(result)


@proxy_bp.route("/youtube", methods=["GET"])
@require_auth
def proxy_youtube():
    """Proxy requests to YouTube oEmbed API."""
    video_url = request.args.get("url")
    if not video_url:
        raise api_error(400, "invalid_input", "url is required")

    # YouTube oEmbed endpoint
    oembed_url = f"https://www.youtube.com/oembed?url={urllib_parse.quote(video_url)}&format=json"

    try:
        data = _fetch_youtube_metadata(oembed_url)
        return json_response(data)
    except HTTPError as e:
        return json_response({"error": str(e)}, status=e.code)
    except URLError as e:
        raise api_error(
            502, "external_error", f"Failed to connect to YouTube: {str(e)}"
        )
    except Exception as e:
        raise api_error(500, "internal_error", str(e))
