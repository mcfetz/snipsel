import json
import logging
from urllib.parse import quote, urlparse

import requests
from pywebpush import WebPushException, webpush
from sqlalchemy import event

from snipsel_api import sse_bus
from snipsel_api.extensions import db
from snipsel_api.models import Notification, PushSubscription, User

logger = logging.getLogger(__name__)


def send_push_notification(user_id: str, payload: dict, commit: bool = True):
    from snipsel_api.config import Settings

    settings = Settings.from_env()

    if not settings.vapid_private_key or not settings.vapid_subject:
        print("[PushService] VAPID keys not configured.")
        return

    # 'sub' claim must be a mailto: link if it's an email address
    vapid_claims = {"sub": settings.vapid_subject}
    if "@" in settings.vapid_subject and not settings.vapid_subject.startswith(
        "mailto:"
    ):
        vapid_claims["sub"] = f"mailto:{settings.vapid_subject}"

    print(f"[PushService] Fetching subscriptions for user {user_id}...")
    subscriptions = (
        db.session.execute(
            db.select(PushSubscription).where(PushSubscription.user_id == user_id)
        )
        .scalars()
        .all()
    )

    print(f"[PushService] Found {len(subscriptions)} subscriptions.")

    for sub in subscriptions:
        sub_info = {
            "endpoint": sub.endpoint,
            "keys": {"p256dh": sub.keys_p256dh, "auth": sub.keys_auth},
        }

        print(f"[PushService] Sending push to endpoint: {sub.endpoint[:30]}...")
        try:
            # pywebpush 2.x requires the 'aud' claim to be the origin of the
            # push endpoint (e.g. https://fcm.googleapis.com for Chrome).
            parsed = urlparse(sub.endpoint)
            endpoint_origin = f"{parsed.scheme}://{parsed.netloc}"
            claims_with_aud: dict[str, str | int] = {
                **vapid_claims,
                "aud": endpoint_origin,
            }

            response = webpush(
                subscription_info=sub_info,
                data=json.dumps(payload),
                vapid_private_key=settings.vapid_private_key,
                vapid_claims=claims_with_aud,
            )
            if isinstance(response, str):
                print(
                    f"[PushService] Push success! Response: {response or 'No Response'}"
                )
            else:
                print(
                    f"[PushService] Push success! Response: {response.status_code if response else 'No Response'}"
                )
        except WebPushException as ex:
            print(f"[PushService] Push failed: {ex}")
            # 410 Gone means subscription is invalid/expired
            if ex.response is not None and ex.response.status_code == 410:
                print("[PushService] Subscription 410 Gone. Deleting...")
                db.session.delete(sub)

    if commit:
        db.session.commit()
    print("[PushService] Done.")


def is_valid_http_url(url: str) -> bool:
    """Return True when ``url`` is a syntactically valid http(s) URL."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.hostname)


def _absolute_url(path: str) -> str | None:
    """Turn a frontend path into an absolute URL for ntfy's ``click`` action."""
    from snipsel_api.config import Settings

    settings = Settings.from_env()
    base = settings.public_base_url or settings.snipsel_frontend_url
    if not base and settings.snipsel_domain:
        base = f"https://{settings.snipsel_domain}"
    if not base:
        return None
    return f"{base.rstrip('/')}/{path.lstrip('/')}"


def send_ntfy_notification(user_id: str, payload: dict, commit: bool = True) -> bool:
    """Publish a notification to the user's configured ntfy server.

    Delivery is best-effort: the function never raises so it cannot break the
    surrounding database transaction. Returns True when ntfy accepted the push.
    """
    user = db.session.get(User, user_id)
    if user is None or not user.ntfy_enabled:
        return False

    base_url = (user.ntfy_url or "").strip()
    topic = (user.ntfy_topic or "").strip()
    if not base_url or not topic:
        print("[NtfyService] ntfy enabled but URL or topic is missing.")
        return False

    if not is_valid_http_url(base_url):
        print("[NtfyService] ntfy URL is not a valid http(s) URL.")
        return False

    target = f"{base_url.rstrip('/')}/{quote(topic.lstrip('/'), safe='')}"

    body: dict[str, str] = {"message": str(payload.get("body") or "")}
    if payload.get("title"):
        body["title"] = str(payload["title"])
    if payload.get("url"):
        absolute = _absolute_url(str(payload["url"]))
        if absolute:
            body["click"] = absolute

    headers = {"Content-Type": "application/json"}
    token = (user.ntfy_token or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.post(target, json=body, headers=headers, timeout=10)
        response.raise_for_status()
        print("[NtfyService] ntfy push delivered.")
        return True
    except requests.RequestException:
        logger.warning("Failed to deliver ntfy notification for user %s", user_id)
        return False


def send_notification(user_id: str, payload: dict, commit: bool = True) -> None:
    """Deliver a notification via the user's configured channels.

    When ntfy is configured it is always used. Web Push is additionally sent
    unless the user chose to replace it with ntfy.
    """
    user = db.session.get(User, user_id)
    ntfy_active = bool(
        user is not None
        and user.ntfy_enabled
        and (user.ntfy_url or "").strip()
        and (user.ntfy_topic or "").strip()
    )

    if ntfy_active:
        send_ntfy_notification(user_id, payload, commit=False)

    if not (ntfy_active and user is not None and user.ntfy_replace_web_push):
        send_push_notification(user_id, payload, commit=False)

    if commit:
        db.session.commit()


def init_push_listeners():
    """Register SQLAlchemy event listeners for push notifications."""

    @event.listens_for(Notification, "after_insert")
    def notification_after_insert(mapper, connection, target: Notification):
        # We use a nested import to avoid circular dependencies
        payload = {
            "title": "Snipsel",
            "body": target.message,
            "url": "/notifications",  # Default landing page
        }

        # Customize URL if linked to a snipsel or collection
        if target.snipsel_id:
            payload["url"] = f"/snipsels/{target.snipsel_id}"
        elif target.collection_id:
            payload["url"] = f"/collections/{target.collection_id}"

        # Trigger the configured push channels (for offline/closed-tab clients).
        # IMPORTANT: Pass commit=False here because we are inside a session flush/commit cycle.
        # Committing here would cause recursive flushes and potential errors.
        send_notification(target.user_id, payload, commit=False)

        # Also notify any open browser tabs via SSE so the badge updates
        # immediately without waiting for the 60-second polling interval.
        # sse_bus.publish() is purely in-memory – safe to call inside a
        # SQLAlchemy event listener.
        sse_bus.publish(
            [target.user_id],
            {
                "type": "notification_created",
                "notification_id": target.id,
                "message": target.message,
            },
        )
