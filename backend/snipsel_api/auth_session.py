from __future__ import annotations

from functools import wraps
from typing import Callable, TypeVar

from flask import Response, g, request, session

from snipsel_api.errors import api_error
from snipsel_api.extensions import db
from snipsel_api.models import User


T = TypeVar("T")


def require_auth(fn: Callable[..., T]) -> Callable[..., T]:
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            raise api_error(401, "unauthorized", "Not logged in")

        user = db.session.get(User, user_id)
        if not user or not user.is_active or user.deleted_at is not None:
            session.pop("user_id", None)
            raise api_error(401, "unauthorized", "Not logged in")

        g.current_user = user
        return fn(*args, **kwargs)

    return wrapper


def require_admin(fn: Callable[..., T]) -> Callable[..., T]:
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user.is_admin:
            raise api_error(403, "forbidden", "Admin access required")
        return fn(*args, **kwargs)

    return wrapper


def current_user() -> User:
    user = getattr(g, "current_user", None)
    if not isinstance(user, User):
        raise api_error(500, "server_error", "Auth context missing")
    return user


def enforce_json(fn: Callable[..., T]) -> Callable[..., T]:
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if request.method in {"POST", "PUT", "PATCH"} and not request.is_json:
            raise api_error(415, "unsupported_media_type", "Expected application/json")
        return fn(*args, **kwargs)

    return wrapper


def json_response(payload: dict, status: int = 200) -> Response:
    from flask import jsonify

    return jsonify(payload), status
