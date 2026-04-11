import json
from urllib.parse import urlparse
from pywebpush import webpush, WebPushException
from sqlalchemy import event

from snipsel_api.extensions import db
from snipsel_api.models import PushSubscription, Notification
from snipsel_api import sse_bus


def send_push_notification(user_id: str, payload: dict, commit: bool = True):
    from snipsel_api.config import Settings
    settings = Settings.from_env()

    if not settings.vapid_private_key or not settings.vapid_subject:
        print("[PushService] VAPID keys not configured.")
        return

    # 'sub' claim must be a mailto: link if it's an email address
    vapid_claims = {"sub": settings.vapid_subject}
    if "@" in settings.vapid_subject and not settings.vapid_subject.startswith("mailto:"):
        vapid_claims["sub"] = f"mailto:{settings.vapid_subject}"

    print(f"[PushService] Fetching subscriptions for user {user_id}...")
    subscriptions = db.session.execute(
        db.select(PushSubscription).where(PushSubscription.user_id == user_id)
    ).scalars().all()

    print(f"[PushService] Found {len(subscriptions)} subscriptions.")

    for sub in subscriptions:
        sub_info = {
            "endpoint": sub.endpoint,
            "keys": {
                "p256dh": sub.keys_p256dh,
                "auth": sub.keys_auth
            }
        }

        print(f"[PushService] Sending push to endpoint: {sub.endpoint[:30]}...")
        try:
            # pywebpush 2.x requires the 'aud' claim to be the origin of the
            # push endpoint (e.g. https://fcm.googleapis.com for Chrome).
            parsed = urlparse(sub.endpoint)
            endpoint_origin = f"{parsed.scheme}://{parsed.netloc}"
            claims_with_aud = {**vapid_claims, "aud": endpoint_origin}

            response = webpush(
                subscription_info=sub_info,
                data=json.dumps(payload),
                vapid_private_key=settings.vapid_private_key,
                vapid_claims=claims_with_aud
            )
            print(f"[PushService] Push success! Response: {response.status_code if response else 'No Response'}")
        except WebPushException as ex:
            print(f"[PushService] Push failed: {ex}")
            # 410 Gone means subscription is invalid/expired
            if ex.response is not None and ex.response.status_code == 410:
                print(f"[PushService] Subscription 410 Gone. Deleting...")
                db.session.delete(sub)

    if commit:
        db.session.commit()
    print("[PushService] Done.")


def init_push_listeners():
    """Register SQLAlchemy event listeners for push notifications."""
    @event.listens_for(Notification, "after_insert")
    def notification_after_insert(mapper, connection, target: Notification):
        # We use a nested import to avoid circular dependencies
        payload = {
            "title": "Snipsel",
            "body": target.message,
            "url": "/notifications" # Default landing page
        }
        
        # Customize URL if linked to a snipsel or collection
        if target.snipsel_id:
            payload["url"] = f"/snipsels/{target.snipsel_id}"
        elif target.collection_id:
            payload["url"] = f"/collections/{target.collection_id}"

        # Trigger the web push (for offline/closed-tab clients)
        # IMPORTANT: Pass commit=False here because we are inside a session flush/commit cycle.
        # Committing here would cause recursive flushes and potential errors.
        send_push_notification(target.user_id, payload, commit=False)

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
