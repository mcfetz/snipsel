from __future__ import annotations

from flask import Blueprint

from snipsel_api.auth_session import current_user, json_response, require_auth
from snipsel_api.extensions import db
from snipsel_api.models import User

users_bp = Blueprint("users", __name__)


@users_bp.get("/users")
@require_auth
def list_users():
    user = current_user()
    rows = (
        db.session.execute(
            db.select(User)
            .where(User.deleted_at.is_(None), User.is_active == True)
            .order_by(User.username.asc())
        )
        .scalars()
        .all()
    )
    return json_response(
        {
            "users": [
                {"id": u.id, "username": u.username}
                for u in rows
                if u.id != user.id or u.id == "public"
            ]
        }
    )
