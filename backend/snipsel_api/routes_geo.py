from __future__ import annotations

from flask import Blueprint, request
from sqlalchemy.orm import joinedload

from snipsel_api.auth_session import current_user, json_response, require_auth
from snipsel_api.errors import api_error
from snipsel_api.extensions import db
from snipsel_api.models import (
    Collection,
    CollectionShare,
    CollectionSnipsel,
    Snipsel,
)

geo_bp = Blueprint("geo", __name__)


@geo_bp.get("/snipsels")
@require_auth
def get_snipsels_by_bounds():
    """Get snipsels within geographic bounds (bounding box)."""
    user = current_user()

    # Parse bounding box parameters
    try:
        ne_lat = float(request.args.get("ne_lat", ""))
        ne_lng = float(request.args.get("ne_lng", ""))
        sw_lat = float(request.args.get("sw_lat", ""))
        sw_lng = float(request.args.get("sw_lng", ""))
    except (ValueError, TypeError):
        raise api_error(
            400,
            "invalid_input",
            "ne_lat, ne_lng, sw_lat, sw_lng are required and must be valid floats",
        )

    # Validate bounds
    if not (-90 <= ne_lat <= 90 and -90 <= sw_lat <= 90):
        raise api_error(400, "invalid_input", "Latitude must be between -90 and 90")
    if not (-180 <= ne_lng <= 180 and -180 <= sw_lng <= 180):
        raise api_error(400, "invalid_input", "Longitude must be between -180 and 180")

    scope = request.args.get("scope", "my")

    query = (
        db.select(Snipsel, Collection)
        .join(CollectionSnipsel, CollectionSnipsel.snipsel_id == Snipsel.id)
        .join(Collection, Collection.id == CollectionSnipsel.collection_id)
    )

    if scope == "shared":
        query = query.join(
            CollectionShare, CollectionShare.collection_id == Collection.id
        ).where(
            Snipsel.deleted_at.is_(None),
            Collection.deleted_at.is_(None),
            CollectionShare.shared_with_user_id == user.id,
            Snipsel.geo_lat.isnot(None),
            Snipsel.geo_lng.isnot(None),
            Snipsel.geo_lat >= sw_lat,
            Snipsel.geo_lat <= ne_lat,
            Snipsel.geo_lng >= sw_lng,
            Snipsel.geo_lng <= ne_lng,
        )
    else:
        query = query.where(
            Snipsel.deleted_at.is_(None),
            Collection.deleted_at.is_(None),
            Snipsel.owner_user_id == user.id,
            Collection.owner_user_id == user.id,
            Snipsel.geo_lat.isnot(None),
            Snipsel.geo_lng.isnot(None),
            Snipsel.geo_lat >= sw_lat,
            Snipsel.geo_lat <= ne_lat,
            Snipsel.geo_lng >= sw_lng,
            Snipsel.geo_lng <= ne_lng,
        )

    query = query.order_by(Snipsel.created_at.desc()).limit(200)

    results = db.session.execute(query).all()

    snipsels_data = []
    seen_snipsel_ids = set()

    for snipsel, collection in results:
        # Avoid duplicates if a snipsel is in multiple collections
        if snipsel.id in seen_snipsel_ids:
            continue
        seen_snipsel_ids.add(snipsel.id)

        # Create excerpt from content (first 100 chars)
        content = snipsel.content_markdown or ""
        excerpt = content[:100] + "..." if len(content) > 100 else content

        snipsels_data.append(
            {
                "id": snipsel.id,
                "lat": snipsel.geo_lat,
                "lng": snipsel.geo_lng,
                "excerpt": excerpt,
                "type": snipsel.type,
                "task_done": snipsel.task_done,
                "collection": {
                    "id": collection.id,
                    "title": collection.title,
                    "icon": collection.icon,
                    "header_color": collection.header_color,
                },
                "created_at": snipsel.created_at.isoformat() + "Z"
                if snipsel.created_at
                else None,
            }
        )

    return json_response(
        {
            "snipsels": snipsels_data,
            "bounds": {
                "ne": {"lat": ne_lat, "lng": ne_lng},
                "sw": {"lat": sw_lat, "lng": sw_lng},
            },
            "count": len(snipsels_data),
        }
    )


@geo_bp.get("/snipsels/all")
@require_auth
def get_all_snipsels_with_geo():
    """Get all snipsels that have geo coordinates (for initial map load)."""
    user = current_user()

    query = (
        db.select(Snipsel, Collection)
        .join(CollectionSnipsel, CollectionSnipsel.snipsel_id == Snipsel.id)
        .join(Collection, Collection.id == CollectionSnipsel.collection_id)
        .where(
            Snipsel.deleted_at.is_(None),
            Collection.deleted_at.is_(None),
            Snipsel.owner_user_id == user.id,
            Collection.owner_user_id == user.id,
            Snipsel.geo_lat.isnot(None),
            Snipsel.geo_lng.isnot(None),
        )
        .order_by(Snipsel.created_at.desc())
        .limit(1000)  # Limit to prevent overwhelming the frontend
    )

    results = db.session.execute(query).all()

    snipsels_data = []
    seen_snipsel_ids = set()

    for snipsel, collection in results:
        if snipsel.id in seen_snipsel_ids:
            continue
        seen_snipsel_ids.add(snipsel.id)

        content = snipsel.content_markdown or ""
        excerpt = content[:100] + "..." if len(content) > 100 else content

        snipsels_data.append(
            {
                "id": snipsel.id,
                "lat": snipsel.geo_lat,
                "lng": snipsel.geo_lng,
                "excerpt": excerpt,
                "type": snipsel.type,
                "task_done": snipsel.task_done,
                "collection": {
                    "id": collection.id,
                    "title": collection.title,
                    "icon": collection.icon,
                    "header_color": collection.header_color,
                },
                "created_at": snipsel.created_at.isoformat() + "Z"
                if snipsel.created_at
                else None,
            }
        )

    return json_response(
        {
            "snipsels": snipsels_data,
            "count": len(snipsels_data),
        }
    )
