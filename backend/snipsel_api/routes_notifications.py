from __future__ import annotations

from flask import Blueprint, request
from snipsel_api.auth_session import (
    current_user,
    enforce_json,
    json_response,
    require_auth,
)
from snipsel_api.extensions import db
from snipsel_api.models import Notification, PushSubscription

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.get("")
@require_auth
def list_notifications():
    user = current_user()

    from snipsel_api.reminders import process_reminders, process_habit_reminders

    process_reminders(user.id)
    process_habit_reminders(user.id)

    q = (
        db.select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
    )

    items = db.session.execute(q).scalars().all()

    out = []
    for n in items:
        out.append(
            {
                "id": n.id,
                "message": n.message,
                "is_read": n.is_read,
                "snipsel_id": n.snipsel_id,
                "collection_id": n.collection_id,
                "created_at": n.created_at.isoformat() + "Z",
            }
        )

    return json_response({"notifications": out})


@notifications_bp.post("/<id>/mark-read")
@require_auth
def mark_read(id: str):
    user = current_user()
    n = db.session.execute(
        db.select(Notification).where(
            Notification.id == id, Notification.user_id == user.id
        )
    ).scalar_one_or_none()

    if n:
        n.is_read = True
        db.session.commit()

    return json_response({"success": True})


@notifications_bp.post("/mark-all-read")
@require_auth
def mark_all_read():
    user = current_user()
    notifications = (
        db.session.execute(
            db.select(Notification).where(
                Notification.user_id == user.id, Notification.is_read == False
            )
        )
        .scalars()
        .all()
    )

    for n in notifications:
        n.is_read = True

    db.session.commit()
    return json_response({"success": True})


@notifications_bp.delete("/read")
@require_auth
def delete_read_notifications():
    user = current_user()

    db.session.execute(
        db.delete(Notification).where(
            Notification.user_id == user.id, Notification.is_read == True
        )
    )

    db.session.commit()
    return json_response({"success": True})


@notifications_bp.get("/vapid-public-key")
@require_auth
def get_vapid_public_key():
    from snipsel_api.config import Settings

    settings = Settings.from_env()
    if not settings.vapid_public_key:
        return json_response({"error": "VAPID not configured"}, 500)
    return json_response({"vapidPublicKey": settings.vapid_public_key})


@notifications_bp.post("/test-push")
@require_auth
def test_push():
    user = current_user()

    from snipsel_api.push_service import send_push_notification

    send_push_notification(
        user.id,
        {
            "title": "Test Notification",
            "body": "It works! 🎉",
            "url": "/api/notifications",
        },
    )

    return json_response({"success": True})


@notifications_bp.post("/subscribe")
@require_auth
@enforce_json
def subscribe():
    user = current_user()
    data = request.json

    subscription = data.get("subscription")
    if not subscription:
        return json_response({"error": "Missing subscription"}, 400)

    endpoint = subscription.get("endpoint")
    keys = subscription.get("keys", {})
    p256dh = keys.get("p256dh")
    auth = keys.get("auth")

    if not endpoint or not p256dh or not auth:
        return json_response({"error": "Invalid subscription data"}, 400)

    existing = db.session.execute(
        db.select(PushSubscription).where(PushSubscription.endpoint == endpoint)
    ).scalar_one_or_none()

    if existing:
        if existing.user_id != user.id:
            existing.user_id = user.id
            existing.keys_p256dh = p256dh
            existing.keys_auth = auth
            db.session.commit()
    else:
        new_sub = PushSubscription(
            user_id=user.id, endpoint=endpoint, keys_p256dh=p256dh, keys_auth=auth
        )
        db.session.add(new_sub)
        db.session.commit()

    return json_response({"success": True})


@notifications_bp.delete("/unsubscribe")
@require_auth
@enforce_json
def unsubscribe():
    user = current_user()
    data = request.json

    endpoint = data.get("endpoint")
    if not endpoint:
        return json_response({"error": "Missing endpoint"}, 400)

    existing = db.session.execute(
        db.select(PushSubscription).where(
            PushSubscription.endpoint == endpoint, PushSubscription.user_id == user.id
        )
    ).scalar_one_or_none()

    if existing:
        db.session.delete(existing)
        db.session.commit()

    return json_response({"success": True})
