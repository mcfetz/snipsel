"""
Simple in-process SSE event bus.

Architecture:
- Each authenticated user has a set of Queue objects – one per open SSE connection.
- When a mutation happens, the route calls sse_bus.publish(user_ids, event, origin_client_id).
- The SSE streaming generator reads from the queue and yields events.
- Events carry an `origin_client_id` field so the originating browser tab can
  ignore its own mutations (it already has the optimistic local update).

Limitations:
- Works only within a single process. Multi-worker Gunicorn deployments would
  need an external broker (e.g. Redis Pub/Sub). For self-hosted single-worker
  use this is transparent and has zero extra dependencies.
  → The Dockerfile intentionally uses -w 1 --threads 4 for this reason.
"""

from __future__ import annotations

import json
import queue
import threading
from typing import Generator

_lock = threading.Lock()
# user_id -> list of (client_id, queue) tuples
_subscribers: dict[str, list[tuple[str, queue.Queue]]] = {}

_SENTINEL = object()  # used to signal disconnect


def subscribe(user_id: str, client_id: str) -> queue.Queue:
    """Register a new SSE connection for *user_id* and return its queue."""
    q: queue.Queue = queue.Queue(maxsize=50)
    with _lock:
        _subscribers.setdefault(user_id, []).append((client_id, q))
    return q


def unsubscribe(user_id: str, q: queue.Queue) -> None:
    """Remove a queue when the SSE connection closes."""
    with _lock:
        entries = _subscribers.get(user_id, [])
        _subscribers[user_id] = [(cid, eq) for cid, eq in entries if eq is not q]
        if not _subscribers[user_id]:
            _subscribers.pop(user_id, None)


def publish(user_ids: list[str], event: dict, origin_client_id: str | None = None) -> None:
    """
    Send *event* to all open SSE connections of the given *user_ids*.

    If *origin_client_id* is supplied it is embedded in the event payload so
    that the originating browser tab can skip refreshing data it already
    updated optimistically.

    Non-blocking: if a queue is full the event is silently dropped for that
    connection (the client will re-sync on the next poll anyway).
    """
    enriched = {**event}
    if origin_client_id:
        enriched["origin_client_id"] = origin_client_id
    payload = json.dumps(enriched, separators=(",", ":"))

    with _lock:
        for uid in user_ids:
            for _cid, q in _subscribers.get(uid, []):
                try:
                    q.put_nowait(payload)
                except queue.Full:
                    pass  # connection is lagging; let frontend resync


def close_all(user_id: str) -> None:
    """Signal all connections for *user_id* to close (e.g. after logout)."""
    with _lock:
        for _cid, q in _subscribers.get(user_id, []):
            try:
                q.put_nowait(_SENTINEL)
            except queue.Full:
                pass


def event_stream(user_id: str, client_id: str, timeout: float = 25.0) -> Generator[str, None, None]:
    """
    Generator that yields SSE-formatted text chunks.

    Keeps the HTTP connection alive with a comment heartbeat every *timeout*
    seconds so proxies / load-balancers don't close idle connections.
    """
    q = subscribe(user_id, client_id)
    try:
        yield ": connected\n\n"  # initial heartbeat / connection confirmation
        while True:
            try:
                item = q.get(timeout=timeout)
            except queue.Empty:
                # Heartbeat – keeps the connection alive through proxies
                yield ": heartbeat\n\n"
                continue

            if item is _SENTINEL:
                break  # server-side close requested

            yield f"data: {item}\n\n"
    finally:
        unsubscribe(user_id, q)
