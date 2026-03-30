from __future__ import annotations

from flask import Blueprint, request
from werkzeug.security import generate_password_hash

from snipsel_api.auth_session import (
    current_user,
    json_response,
    require_admin,
    require_auth,
)
from snipsel_api.errors import api_error
from snipsel_api.extensions import db
from snipsel_api.models import User

admin_bp = Blueprint("admin", __name__)


def _user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_admin": user.is_admin,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() + "Z" if user.created_at else None,
        "last_login": None,
    }


@admin_bp.get("/users")
@require_auth
@require_admin
def list_users():
    users = (
        db.session.execute(
            db.select(User).where(User.deleted_at.is_(None)).order_by(User.username)
        )
        .scalars()
        .all()
    )
    return json_response({"users": [_user_to_dict(u) for u in users]})


@admin_bp.post("/users")
@require_auth
@require_admin
def create_user():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    is_admin = data.get("is_admin", False)

    if not username or not email or not password:
        raise api_error(
            400, "missing_fields", "Username, email and password are required"
        )

    if len(password) < 8:
        raise api_error(
            400, "password_too_short", "Password must be at least 8 characters"
        )

    existing = (
        db.session.execute(
            db.select(User).where((User.username == username) | (User.email == email))
        )
        .scalars()
        .first()
    )
    if existing:
        raise api_error(400, "duplicate_user", "Username or email already exists")

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        is_admin=is_admin,
    )
    db.session.add(user)
    db.session.commit()

    return json_response({"user": _user_to_dict(user)})


@admin_bp.delete("/users/<user_id>")
@require_auth
@require_admin
def delete_user(user_id: str):
    if user_id == current_user().id:
        raise api_error(400, "cannot_delete_self", "You cannot delete your own account")

    user = db.session.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise api_error(404, "user_not_found", "User not found")

    user.deleted_at = db.func.now()
    db.session.commit()

    return json_response({"ok": True})


@admin_bp.patch("/users/<user_id>")
@require_auth
@require_admin
def update_user(user_id: str):
    user = db.session.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise api_error(404, "user_not_found", "User not found")

    data = request.get_json() or {}

    if "is_admin" in data:
        user.is_admin = bool(data["is_admin"])

    if "is_active" in data:
        user.is_active = bool(data["is_active"])

    db.session.commit()
    return json_response({"user": _user_to_dict(user)})
