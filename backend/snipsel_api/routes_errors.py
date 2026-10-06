from __future__ import annotations

from typing import Any

from flask import Blueprint

from snipsel_api.auth_session import json_response
from snipsel_api.errors import ApiError

errors_bp = Blueprint("errors", __name__)


@errors_bp.app_errorhandler(ApiError)
def handle_api_error(err: ApiError):
    payload: dict[str, dict[str, Any]] = {
        "error": {"code": err.code, "message": err.message}
    }
    if err.details:
        payload["error"]["details"] = err.details
    return json_response(payload, status=err.status_code)
