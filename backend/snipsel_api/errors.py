from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ApiError(Exception):
    status_code: int
    code: str
    message: str
    details: dict[str, Any] | None = None


def api_error(
    status_code: int, code: str, message: str, details: dict[str, Any] | None = None
) -> ApiError:
    return ApiError(
        status_code=status_code, code=code, message=message, details=details
    )
