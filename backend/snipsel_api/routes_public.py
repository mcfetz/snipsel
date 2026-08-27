from __future__ import annotations
import uuid
import re
from flask import Blueprint, request, session, current_app
from snipsel_api.extensions import db
from snipsel_api.models import Collection, Snipsel, User, Attachment, CollectionSnipsel, CollectionShare
from snipsel_api.auth_session import json_response
from snipsel_api.errors import api_error
from datetime import datetime
from sqlalchemy import func
from snipsel_api.routes_snipsels import _collection_item_json, _sync_backlinks, _sync_tags_mentions

public_bp = Blueprint("public", __name__)

def _get_public_collection(token: str) -> Collection:
    c = db.session.execute(
        db.select(Collection).where(Collection.public_token == token, Collection.deleted_at.is_(None))
    ).scalars().first()
    if not c:
        raise api_error(404, "not_found", "Collection not found")
    return c

def _check_passcode(collection: Collection):
    if not collection.is_passcode_protected:
        return
    
    verified_cid = session.get("public_passcode_verified_collection_id")
    if verified_cid == collection.id:
        return
        
    raise api_error(403, "passcode_required", "Passcode required")
    
def _log_public_access(collection_id: str):
    allowed = session.get("public_authorized_collections")
    if not isinstance(allowed, list):
        allowed = []
    if collection_id not in allowed:
        allowed.append(collection_id)
        session["public_authorized_collections"] = allowed

@public_bp.get("/collections/<token>")
def get_public_collection(token: str):
    c = _get_public_collection(token)
    
    # We don't check passcode here, but the frontend will see "is_passcode_protected" 
    # and know it needs to verify first.
    
    # Check if currently unlocked in session
    is_unlocked = not c.is_passcode_protected or session.get("public_passcode_verified_collection_id") == c.id

    if not c.is_passcode_protected:
        _log_public_access(c.id)

    return json_response({
        "collection": {
            "id": c.id,
            "title": c.title,
            "icon": c.icon,
            "header_color": c.header_color,
            "header_image_url": c.header_image_url,
            "header_image_position": c.header_image_position,
            "header_image_x_position": c.header_image_x_position,
            "header_image_zoom": c.header_image_zoom,
            "is_passcode_protected": c.is_passcode_protected,
            "is_unlocked": is_unlocked,
            "default_snipsel_type": c.default_snipsel_type,
            "view_mode": c.view_mode or "list",
        }
    })

@public_bp.post("/collections/<token>/passcode/verify")
def verify_public_passcode(token: str):
    c = _get_public_collection(token)
    data = request.get_json() or {}
    passcode = data.get("passcode")
    
    if not c.is_passcode_protected:
        return json_response({"ok": True})
        
    owner = c.owner
    # Use the owner's passcode for the collection
    from werkzeug.security import check_password_hash
    if not owner.passcode_hash or not check_password_hash(owner.passcode_hash, passcode):
        raise api_error(401, "invalid_passcode", "Invalid passcode")
        
    session["public_passcode_verified_collection_id"] = c.id
    _log_public_access(c.id)
    return json_response({"ok": True})

@public_bp.get("/collections/<token>/snipsels")
def list_public_snipsels(token: str):
    c = _get_public_collection(token)
    _check_passcode(c)
    
    items = (
        db.session.execute(
            db.select(CollectionSnipsel)
            .join(Snipsel, Snipsel.id == CollectionSnipsel.snipsel_id)
            .where(CollectionSnipsel.collection_id == c.id, Snipsel.deleted_at.is_(None))
            .order_by(CollectionSnipsel.position.asc())
        )
        .scalars()
        .all()
    )
    
    # Check if "public" user has write access
    public_share = db.session.execute(
        db.select(CollectionShare).where(
            CollectionShare.collection_id == c.id,
            CollectionShare.shared_with_user_id == "public"
        )
    ).scalars().first()
    
    can_write = public_share and public_share.permission == "write"

    return json_response({
        "items": [_collection_item_json(it, "public") for it in items],
        "can_write": bool(can_write)
    })

@public_bp.post("/collections/<token>/snipsels")
def public_create_snipsel(token: str):
    c = _get_public_collection(token)
    _check_passcode(c)

    share = db.session.execute(
        db.select(CollectionShare).where(
            CollectionShare.collection_id == c.id,
            CollectionShare.shared_with_user_id == "public",
        )
    ).scalar_one_or_none()

    if not share or share.permission != "write":
        raise api_error(403, "forbidden", "You do not have write access to this collection")

    data = request.get_json() or {}
    snipsel_type = data.get("type") or c.default_snipsel_type or "text"
    content_markdown = data.get("content_markdown")

    s = Snipsel(
        owner_user_id=c.owner_user_id,
        type=snipsel_type,
        content_markdown=content_markdown,
        created_by_id="public",
        modified_by_id="public",
    )
    db.session.add(s)
    db.session.flush()

    indent = data.get("indent", 0)
    max_pos = (
        db.session.execute(
            db.select(func.max(CollectionSnipsel.position)).where(CollectionSnipsel.collection_id == c.id)
        ).scalar()
        or 0
    )
    cs = CollectionSnipsel(collection_id=c.id, snipsel_id=s.id, position=max_pos + 1, indent=indent)
    db.session.add(cs)

    # Sync using owner_user_id so they end up in the owner's tag/mention space
    _sync_tags_mentions(user_id=c.owner_user_id, snipsel=s)
    _sync_backlinks(user_id=c.owner_user_id, snipsel=s)
    db.session.commit()

    return json_response({"item": _collection_item_json(cs, "public")}, status=201)


@public_bp.patch("/collections/<token>/snipsels/<snipsel_id>")
def public_patch_snipsel(token: str, snipsel_id: str):
    c = _get_public_collection(token)
    _check_passcode(c)

    share = db.session.execute(
        db.select(CollectionShare).where(
            CollectionShare.collection_id == c.id,
            CollectionShare.shared_with_user_id == "public",
        )
    ).scalar_one_or_none()

    if not share or share.permission != "write":
        raise api_error(403, "forbidden", "You do not have write access to this collection")

    cs = db.session.execute(
        db.select(CollectionSnipsel).where(
            CollectionSnipsel.collection_id == c.id,
            CollectionSnipsel.snipsel_id == snipsel_id
        )
    ).scalar_one_or_none()
    
    if not cs:
        raise api_error(404, "not_found", "Snipsel not found in this collection")

    s = cs.snipsel
    data = request.get_json() or {}

    if "content_markdown" in data:
        s.content_markdown = data["content_markdown"]
    if "type" in data:
        s.type = data["type"]
    if "task_done" in data:
        s.task_done = bool(data["task_done"])
    
    s.modified_by_id = "public"
    s.modified_at = datetime.utcnow()

    _sync_tags_mentions(user_id=c.owner_user_id, snipsel=s)
    _sync_backlinks(user_id=c.owner_user_id, snipsel=s)
    db.session.commit()

    return json_response({"item": _collection_item_json(cs, "public")})


@public_bp.delete("/collections/<token>/snipsels/<snipsel_id>")
def public_delete_snipsel(token: str, snipsel_id: str):
    c = _get_public_collection(token)
    _check_passcode(c)

    share = db.session.execute(
        db.select(CollectionShare).where(
            CollectionShare.collection_id == c.id,
            CollectionShare.shared_with_user_id == "public",
        )
    ).scalar_one_or_none()

    if not share or share.permission != "write":
        raise api_error(403, "forbidden", "You do not have write access to this collection")

    cs = db.session.execute(
        db.select(CollectionSnipsel).where(
            CollectionSnipsel.collection_id == c.id,
            CollectionSnipsel.snipsel_id == snipsel_id
        )
    ).scalar_one_or_none()
    
    if not cs:
        raise api_error(404, "not_found", "Snipsel not found in this collection")

    # We only remove it from the collection publicly
    # Or should we delete the snipsel? 
    # Usually in Snipsel, deleting from a collection often means archiving the snipsel if it's not elsewhere.
    # For simplicity and safety, we'll just remove the link for now.
    db.session.delete(cs)
    db.session.commit()

    return json_response({"ok": True})
