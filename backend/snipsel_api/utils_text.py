from __future__ import annotations

import re

_TRAILING_PUNCT_RE = re.compile(r"[\]\[\)\}\.,;:!?]+$")


def normalize_token(raw: str) -> str:
    return raw.casefold()


def extract_tags(text: str) -> set[str]:
    return _extract_prefixed(text, "#")


def extract_mentions(text: str) -> set[str]:
    return _extract_prefixed(text, "@")


def _extract_prefixed(text: str, prefix: str) -> set[str]:
    if not text:
        return set()

    out: set[str] = set()
    for part in re.split(r"\s+", text):
        if not part.startswith(prefix) or len(part) == 1:
            continue
        token = part[1:]
        if not token or not token[:1].isalpha():
            continue
        token = _TRAILING_PUNCT_RE.sub("", token)
        if not token:
            continue
        out.add(normalize_token(token))
    return out


_COLLECTION_REF_RE = re.compile(r'\[\[([^\[\]]+)\]\]')


def extract_collection_refs(text: str) -> set[str]:
    if not text:
        return set()

    out: set[str] = set()
    for m in _COLLECTION_REF_RE.finditer(text):
        title = m.group(1).strip()
        if title:
            out.add(title)
    return out
