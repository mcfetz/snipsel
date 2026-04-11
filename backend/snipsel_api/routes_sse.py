"""
SSE endpoint for real-time updates.

Clients connect to GET /api/sse/events?client_id=<uuid> and receive a
long-lived text/event-stream response. The server pushes lightweight
notification events (JSON) whenever collections or snipsels are mutated.
Clients then decide whether to re-fetch based on what they currently display.

Event shapes:
  {"type": "collection_updated", "ids": ["<col_id>"], "origin_client_id": "<uuid>"}
  {"type": "collection_list_changed", "origin_client_id": "<uuid>"}
  {"type": "snipsels_updated", "collection_id": "<id>", "ids": [...], "origin_client_id": "<uuid>"}

The `origin_client_id` field lets the originating tab skip re-fetching data
it already updated optimistically.
"""

from __future__ import annotations

import uuid

from flask import Blueprint, Response, request, stream_with_context

from snipsel_api.auth_session import current_user, require_auth
from snipsel_api import sse_bus

sse_bp = Blueprint("sse", __name__)


@sse_bp.get("/events")
@require_auth
def sse_events():
    user = current_user()
    user_id = user.id
    # The client supplies its own stable random ID so the server can embed it
    # in events. The client then ignores events it originated itself.
    client_id = request.args.get("client_id") or str(uuid.uuid4())

    return Response(
        stream_with_context(sse_bus.event_stream(user_id, client_id)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # nginx: disable proxy buffering
            "Connection": "keep-alive",
        },
    )
