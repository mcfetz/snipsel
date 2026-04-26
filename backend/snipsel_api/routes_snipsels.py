from __future__ import annotations

import re
from datetime import datetime
from dateutil import rrule

from flask import Blueprint, request

from snipsel_api.auth_session import (
    current_user,
    enforce_json,
    json_response,
    require_auth,
)
from snipsel_api.errors import api_error
from snipsel_api.extensions import db
from snipsel_api.permissions import (
    can_read_collection,
    can_write_collection,
    can_read_snipsel_via_collections,
    can_write_snipsel_via_collections,
    is_passcode_unlocked,
)
from snipsel_api.routes_search import clear_search_cache

from snipsel_api.models import (
    Attachment,
    CollectionSnipsel,
    Collection,
    CollectionShare,
    Mention,
    Snipsel,
    SnipselCollectionRef,
    SnipselLink,
    SnipselMention,
    SnipselReaction,
    SnipselTag,
    Tag,
    User,
    Notification,
)
from snipsel_api import sse_bus


def _touch_collections_for_snipsel(*, snipsel_id: str, modified_by_id: str) -> None:
    now = datetime.utcnow()
    collection_ids = (
        db.session.execute(
            db.select(CollectionSnipsel.collection_id).where(
                CollectionSnipsel.snipsel_id == snipsel_id
            )
        )
        .scalars()
        .all()
    )
    if not collection_ids:
        return
    db.session.execute(
        db.update(Collection)
        .where(Collection.id.in_(collection_ids), Collection.deleted_at.is_(None))
        .values(modified_at=now, modified_by_id=modified_by_id)
    )


def _is_empty_snipsel(s: Snipsel) -> bool:
    has_content = bool(s.content_markdown and s.content_markdown.strip())
    has_url = bool(s.external_url and s.external_url.strip())
    has_attachments = len(s.attachments) > 0
    return not has_content and not has_url and not has_attachments


def _hard_delete_snipsel(s: Snipsel) -> None:
    from snipsel_api.routes_attachments import delete_attachment_file

    for att in s.attachments:
        delete_attachment_file(att)

    db.session.execute(
        db.delete(CollectionSnipsel).where(CollectionSnipsel.snipsel_id == s.id)
    )
    db.session.execute(
        db.delete(SnipselCollectionRef).where(SnipselCollectionRef.snipsel_id == s.id)
    )
    db.session.execute(
        db.delete(SnipselLink).where(
            db.or_(
                SnipselLink.from_snipsel_id == s.id, SnipselLink.to_snipsel_id == s.id
            )
        )
    )
    db.session.execute(db.delete(SnipselTag).where(SnipselTag.snipsel_id == s.id))
    db.session.execute(
        db.delete(SnipselMention).where(SnipselMention.snipsel_id == s.id)
    )
    db.session.execute(
        db.delete(SnipselReaction).where(SnipselReaction.snipsel_id == s.id)
    )
    db.session.execute(db.delete(Notification).where(Notification.snipsel_id == s.id))
    db.session.delete(s)


from sqlalchemy.orm import joinedload, selectinload
from snipsel_api.utils_text import (
    extract_collection_refs,
    extract_mentions,
    extract_tags,
)

snipsels_bp = Blueprint("snipsels", __name__)


def _snipsel_collection_user_ids(collection_id: str) -> list[str]:
    """Return IDs of all users who have access to *collection_id* (owner + shares)."""
    col = db.session.get(Collection, collection_id)
    if not col:
        return []
    ids = [col.owner_user_id]
    share_ids = (
        db.session.execute(
            db.select(CollectionShare.shared_with_user_id).where(
                CollectionShare.collection_id == collection_id
            )
        )
        .scalars()
        .all()
    )
    ids.extend(share_ids)
    return ids


@snipsels_bp.get("/collections/<collection_id>/snipsels")
@require_auth
def list_collection_snipsels(collection_id: str):
    user = current_user()
    if not can_read_collection(user.id, collection_id):
        raise api_error(404, "not_found", "Collection not found")

    c = db.session.get(Collection, collection_id)
    if not c or c.deleted_at is not None:
        raise api_error(404, "not_found", "Collection not found")

    if c.is_passcode_protected and not is_passcode_unlocked(collection_id):
        raise api_error(
            403, "passcode_required", "This collection is passcode protected"
        )

    items = (
        db.session.execute(
            db.select(CollectionSnipsel)
            .join(Snipsel, Snipsel.id == CollectionSnipsel.snipsel_id)
            .options(
                joinedload(CollectionSnipsel.snipsel).joinedload(Snipsel.created_by),
                joinedload(CollectionSnipsel.snipsel).joinedload(Snipsel.modified_by),
                joinedload(CollectionSnipsel.snipsel).joinedload(Snipsel.done_by),
                joinedload(CollectionSnipsel.snipsel).selectinload(Snipsel.reactions),
                joinedload(CollectionSnipsel.snipsel).selectinload(Snipsel.attachments),
            )
            .where(
                CollectionSnipsel.collection_id == collection_id,
                Snipsel.deleted_at.is_(None),
            )
            .order_by(CollectionSnipsel.position.asc())
        )
        .scalars()
        .unique()
        .all()
    )

    snipsel_ids = [cs.snipsel_id for cs in items]
    refs_by_snipsel_id = {sid: [] for sid in snipsel_ids}
    if snipsel_ids:
        all_refs = (
            db.session.execute(
                db.select(SnipselCollectionRef)
                .join(Collection, Collection.id == SnipselCollectionRef.collection_id)
                .options(joinedload(SnipselCollectionRef.collection))
                .where(
                    SnipselCollectionRef.snipsel_id.in_(snipsel_ids),
                    Collection.deleted_at.is_(None),
                )
            )
            .scalars()
            .all()
        )
        for r in all_refs:
            refs_by_snipsel_id[r.snipsel_id].append(r)

    return json_response(
        {
            "items": [
                _collection_item_json(cs, user.id, refs_by_snipsel_id[cs.snipsel_id])
                for cs in items
            ]
        }
    )


@snipsels_bp.post("/collections/<collection_id>/snipsels")
@require_auth
@enforce_json
def create_snipsel(collection_id: str):
    user = current_user()
    if not can_write_collection(user.id, collection_id):
        raise api_error(404, "not_found", "Collection not found")
    data = request.get_json() or {}

    snipsel_type = data.get("type")
    if not snipsel_type:
        col = (
            db.session.execute(
                db.select(Collection).where(
                    Collection.id == collection_id,
                    Collection.owner_user_id == user.id,
                    Collection.deleted_at.is_(None),
                )
            )
            .scalars()
            .first()
        )
        snipsel_type = (
            col.default_snipsel_type if col and col.default_snipsel_type else "text"
        )
    content_markdown = data.get("content_markdown")

    geo_lat = data.get("geo_lat")
    geo_lng = data.get("geo_lng")
    geo_accuracy_m = data.get("geo_accuracy_m")

    s = Snipsel(
        owner_user_id=user.id,
        type=snipsel_type,
        card_view=data.get("card_view", True),
        content_markdown=content_markdown,
        geo_lat=float(geo_lat) if geo_lat is not None else None,
        geo_lng=float(geo_lng) if geo_lng is not None else None,
        geo_accuracy_m=float(geo_accuracy_m) if geo_accuracy_m is not None else None,
        reminder_at=datetime.fromisoformat(data["reminder_at"].replace("Z", ""))
        if data.get("reminder_at")
        else None,
        reminder_rrule=data.get("reminder_rrule"),
        created_by_id=user.id,
        modified_by_id=user.id,
    )
    db.session.add(s)
    db.session.flush()

    indent = data.get("indent", 0)

    max_pos = (
        db.session.execute(
            db.select(db.func.max(CollectionSnipsel.position)).where(
                CollectionSnipsel.collection_id == collection_id
            )
        ).scalar()
        or 0
    )
    cs = CollectionSnipsel(
        collection_id=collection_id,
        snipsel_id=s.id,
        position=max_pos + 1,
        indent=indent,
    )
    db.session.add(cs)

    _sync_tags_mentions(user_id=user.id, snipsel=s)
    _sync_backlinks(user_id=user.id, snipsel=s)
    clear_search_cache(user.id)
    db.session.commit()
    # Notify all users with access to this collection
    sse_bus.publish(
        _snipsel_collection_user_ids(collection_id),
        {"type": "snipsels_updated", "collection_id": collection_id, "ids": [s.id]},
        origin_client_id=request.headers.get("X-Client-Id"),
    )
    return json_response({"item": _collection_item_json(cs, user.id)}, status=201)


@snipsels_bp.post("/collections/<collection_id>/snipsels/<snipsel_id>/reference")
@require_auth
def reference_snipsel(collection_id: str, snipsel_id: str):
    user = current_user()
    data = request.get_json(silent=True) or {}
    s = _get_owned_snipsel(user.id, snipsel_id)
    if not can_write_collection(user.id, collection_id):
        raise api_error(404, "not_found", "Collection not found")

    exists = (
        db.session.execute(
            db.select(CollectionSnipsel).where(
                CollectionSnipsel.collection_id == collection_id,
                CollectionSnipsel.snipsel_id == snipsel_id,
            )
        )
        .scalars()
        .first()
    )
    if exists:
        return json_response({"item": _collection_item_json(exists, user.id)})

    indent = data.get("indent", 0)

    max_pos = (
        db.session.execute(
            db.select(db.func.max(CollectionSnipsel.position)).where(
                CollectionSnipsel.collection_id == collection_id
            )
        ).scalar()
        or 0
    )
    cs = CollectionSnipsel(
        collection_id=collection_id,
        snipsel_id=s.id,
        position=max_pos + 1,
        indent=indent,
    )
    db.session.add(cs)
    db.session.execute(
        db.update(Collection)
        .where(Collection.id == collection_id, Collection.deleted_at.is_(None))
        .values(modified_at=datetime.utcnow(), modified_by_id=user.id)
    )
    clear_search_cache(user.id)
    db.session.commit()
    return json_response({"item": _collection_item_json(cs)}, status=201)


@snipsels_bp.post("/collections/<collection_id>/snipsels/<snipsel_id>/copy")
@require_auth
def copy_snipsel(collection_id: str, snipsel_id: str):
    user = current_user()
    data = request.get_json(silent=True) or {}
    if not can_write_collection(user.id, collection_id):
        raise api_error(404, "not_found", "Collection not found")

    src = db.session.get(Snipsel, snipsel_id)
    if not src or src.deleted_at is not None:
        raise api_error(404, "not_found", "Snipsel not found")
    if src.owner_user_id != user.id and not can_read_snipsel_via_collections(
        user.id, snipsel_id
    ):
        raise api_error(404, "not_found", "Snipsel not found")

    s = Snipsel(
        owner_user_id=user.id,
        type=src.type,
        content_markdown=src.content_markdown,
        task_done=src.task_done,
        done_at=src.done_at,
        done_by_id=src.done_by_id,
        external_url=src.external_url,
        external_label=src.external_label,
        internal_target_snipsel_id=src.internal_target_snipsel_id,
        reminder_at=src.reminder_at,
        reminder_rrule=src.reminder_rrule,
        created_by_id=user.id,
        modified_by_id=user.id,
    )
    db.session.add(s)
    db.session.flush()

    indent = data.get("indent", 0)

    max_pos = (
        db.session.execute(
            db.select(db.func.max(CollectionSnipsel.position)).where(
                CollectionSnipsel.collection_id == collection_id
            )
        ).scalar()
        or 0
    )
    cs = CollectionSnipsel(
        collection_id=collection_id,
        snipsel_id=s.id,
        position=max_pos + 1,
        indent=indent,
    )
    db.session.add(cs)
    _sync_tags_mentions(user_id=user.id, snipsel=s)
    _sync_backlinks(user_id=user.id, snipsel=s)
    clear_search_cache(user.id)
    db.session.commit()
    return json_response({"item": _collection_item_json(cs, user.id)}, status=201)


@snipsels_bp.get("/snipsels/<snipsel_id>")
@require_auth
def get_snipsel(snipsel_id: str):
    user = current_user()
    s = (
        db.session.execute(
            db.select(Snipsel)
            .options(
                joinedload(Snipsel.created_by),
                joinedload(Snipsel.modified_by),
                joinedload(Snipsel.done_by),
                joinedload(Snipsel.reactions),
            )
            .where(Snipsel.id == snipsel_id)
        )
        .scalars()
        .unique()
        .first()
    )
    if not s or s.deleted_at is not None:
        raise api_error(404, "not_found", "Snipsel not found")

    can_read = s.owner_user_id == user.id or can_read_snipsel_via_collections(
        user.id, snipsel_id
    )
    if not can_read:
        uname = (getattr(user, "username", "") or "").strip().casefold()
        if not uname:
            raise api_error(404, "not_found", "Snipsel not found")
        is_mentioned = (
            db.session.execute(
                db.select(db.func.count())
                .select_from(SnipselMention)
                .join(Mention, Mention.id == SnipselMention.mention_id)
                .where(SnipselMention.snipsel_id == snipsel_id, Mention.name == uname)
            ).scalar()
            or 0
        )
        if is_mentioned <= 0:
            raise api_error(404, "not_found", "Snipsel not found")

    has_collection_access = (
        s.owner_user_id == user.id
        or can_read_snipsel_via_collections(user.id, snipsel_id)
    )
    has_write_access = s.owner_user_id == user.id or can_write_snipsel_via_collections(
        user.id, snipsel_id
    )
    placements = (
        db.session.execute(
            db.select(CollectionSnipsel)
            .join(Collection, Collection.id == CollectionSnipsel.collection_id)
            .where(
                CollectionSnipsel.snipsel_id == snipsel_id,
                Collection.owner_user_id == user.id,
                Collection.deleted_at.is_(None),
            )
        )
        .scalars()
        .all()
    )

    backlinks = (
        db.session.execute(
            db.select(SnipselLink).where(SnipselLink.to_snipsel_id == snipsel_id)
        )
        .scalars()
        .all()
    )

    tag_names = (
        db.session.execute(
            db.select(Tag.name)
            .join(SnipselTag, SnipselTag.tag_id == Tag.id)
            .where(Tag.owner_user_id == user.id, SnipselTag.snipsel_id == snipsel_id)
            .order_by(Tag.name.asc())
        )
        .scalars()
        .all()
    )

    mention_names = (
        db.session.execute(
            db.select(Mention.name)
            .join(SnipselMention, SnipselMention.mention_id == Mention.id)
            .where(
                Mention.owner_user_id == user.id,
                SnipselMention.snipsel_id == snipsel_id,
            )
            .order_by(Mention.name.asc())
        )
        .scalars()
        .all()
    )

    can_toggle_task_done = bool(
        s.type == "task" and (has_collection_access or is_mentioned)
    )

    return json_response(
        {
            "snipsel": _snipsel_json(s, user.id),
            "has_collection_access": bool(has_collection_access),
            "has_write_access": bool(has_write_access),
            "can_toggle_task_done": bool(can_toggle_task_done),
            "tags": [n for n in tag_names if n and n[:1].isalpha()],
            "mentions": [n for n in mention_names if n and n[:1].isalpha()],
            "placements": [
                {
                    "collection_id": cs.collection_id,
                    "collection_title": cs.collection.title,
                    "collection_icon": cs.collection.icon,
                    "position": cs.position,
                    "indent": cs.indent,
                }
                for cs in placements
            ],
            "backlinks": [
                {
                    "from_snipsel_id": l.from_snipsel_id,
                    "to_snipsel_id": l.to_snipsel_id,
                }
                for l in backlinks
            ],
        }
    )


@snipsels_bp.patch("/snipsels/<snipsel_id>")
@require_auth
@enforce_json
def update_snipsel(snipsel_id: str):
    user = current_user()
    s = db.session.get(Snipsel, snipsel_id)
    if not s or s.deleted_at is not None:
        raise api_error(404, "not_found", "Snipsel not found")
    has_collection_access = (
        s.owner_user_id == user.id
        or can_read_snipsel_via_collections(user.id, snipsel_id)
    )
    has_write_access = s.owner_user_id == user.id or can_write_snipsel_via_collections(
        user.id, snipsel_id
    )

    uname = (getattr(user, "username", "") or "").strip().casefold()
    is_mentioned = False
    if uname:
        is_mentioned = (
            db.session.execute(
                db.select(db.func.count())
                .select_from(SnipselMention)
                .join(Mention, Mention.id == SnipselMention.mention_id)
                .where(SnipselMention.snipsel_id == snipsel_id, Mention.name == uname)
            ).scalar()
            or 0
        ) > 0

    can_toggle_task_done = bool(
        s.type == "task" and (has_collection_access or is_mentioned)
    )

    if not has_write_access:
        if not (can_toggle_task_done and "task_done" in (request.get_json() or {})):
            raise api_error(404, "not_found", "Snipsel not found")
    data = request.get_json() or {}

    old_type = s.type
    if "type" in data and has_write_access:
        new_type = data.get("type")
        if isinstance(new_type, str) and new_type:
            s.type = new_type
    if "card_view" in data and has_write_access:
        s.card_view = bool(data.get("card_view", True))
    if "content_markdown" in data and has_write_access:
        s.content_markdown = data.get("content_markdown")
    if "task_done" in data:
        val = data.get("task_done")
        if isinstance(val, bool):
            status = 1 if val else 0
        else:
            try:
                status = int(val)
            except (ValueError, TypeError):
                status = 0
        
        old_status = int(s.task_done)
        s.task_done = status
        
        if status in {1, 2}:
            s.done_at = datetime.utcnow()
            s.done_by_id = user.id
            
            # Completion notification and recurrence only for status 1 (Done)
            if status == 1 and old_status == 0:
                if user.id != s.created_by_id and s.created_by_id:
                    task_preview = _get_task_preview(s.content_markdown or "")
                    msg = (
                        f"{user.username} completed a task you created: {task_preview}"
                        if task_preview
                        else f"{user.username} completed a task you created."
                    )
                    if not _is_snipsel_muted(s.id):
                        n = Notification(
                            user_id=s.created_by_id, message=msg, snipsel_id=s.id
                        )
                        db.session.add(n)

                # Handle recurrence: Create a copy if it has an rrule
                if s.reminder_rrule and s.reminder_at:
                    try:
                        rr = rrule.rrulestr(s.reminder_rrule, dtstart=s.reminder_at)
                        next_at = rr.after(s.reminder_at)
                        if next_at:
                            # Create new snipsel
                            new_s = Snipsel(
                                type=s.type,
                                card_view=s.card_view,
                                content_markdown=s.content_markdown,
                                owner_user_id=s.owner_user_id,
                                created_by_id=user.id,
                                modified_by_id=user.id,
                                external_url=s.external_url,
                                external_label=s.external_label,
                                internal_target_snipsel_id=s.internal_target_snipsel_id,
                                reminder_at=next_at,
                                reminder_rrule=s.reminder_rrule,
                                geo_lat=s.geo_lat,
                                geo_lng=s.geo_lng,
                                geo_accuracy_m=s.geo_accuracy_m,
                            )
                            db.session.add(new_s)
                            db.session.flush()  # Get new_s.id

                            # Copy tags and mentions
                            for t in s.tags:
                                db.session.add(
                                    SnipselTag(snipsel_id=new_s.id, tag_id=t.tag_id)
                                )
                            for m in s.mentions:
                                db.session.add(
                                    SnipselMention(
                                        snipsel_id=new_s.id, mention_id=m.mention_id
                                    )
                                )

                            # Insert into same collections at position + 1
                            placements = (
                                db.session.execute(
                                    db.select(CollectionSnipsel).where(
                                        CollectionSnipsel.snipsel_id == s.id
                                    )
                                )
                                .scalars()
                                .all()
                            )

                            for p in placements:
                                # Shift others
                                db.session.execute(
                                    db.update(CollectionSnipsel)
                                    .where(
                                        CollectionSnipsel.collection_id == p.collection_id,
                                        CollectionSnipsel.position > p.position,
                                    )
                                    .values(position=CollectionSnipsel.position + 1)
                                )
                                # Add new placement
                                new_p = CollectionSnipsel(
                                    collection_id=p.collection_id,
                                    snipsel_id=new_s.id,
                                    position=p.position + 1,
                                    indent=p.indent,
                                )
                                db.session.add(new_p)
                    except Exception as e:
                        # Log error but don't fail completion
                        print(f"Error handling recurrence for snipsel {s.id}: {e}")
        else:
            s.done_at = None
            s.done_by_id = None
    if "external_url" in data and has_write_access:
        s.external_url = data.get("external_url")
    if "external_label" in data and has_write_access:
        s.external_label = data.get("external_label")
    if "internal_target_snipsel_id" in data and has_write_access:
        s.internal_target_snipsel_id = data.get("internal_target_snipsel_id")
    if "reminder_at" in data and has_write_access:
        val = data.get("reminder_at")
        s.reminder_at = datetime.fromisoformat(val.replace("Z", "")) if val else None
    if "reminder_rrule" in data and has_write_access:
        s.reminder_rrule = data.get("reminder_rrule")

    s.modified_by_id = user.id
    if has_write_access:
        _sync_tags_mentions(
            user_id=s.owner_user_id,
            snipsel=s,
            newly_became_task=(old_type != "task" and s.type == "task"),
        )
    _touch_collections_for_snipsel(snipsel_id=snipsel_id, modified_by_id=user.id)
    clear_search_cache(user.id)
    db.session.commit()
    # Notify all collection members about the updated snipsel
    affected_collection_ids = (
        db.session.execute(
            db.select(CollectionSnipsel.collection_id).where(
                CollectionSnipsel.snipsel_id == snipsel_id
            )
        )
        .scalars()
        .all()
    )
    for cid in affected_collection_ids:
        sse_bus.publish(
            _snipsel_collection_user_ids(cid),
            {"type": "snipsels_updated", "collection_id": cid, "ids": [snipsel_id]},
            origin_client_id=request.headers.get("X-Client-Id"),
        )
    return json_response({"snipsel": _snipsel_json(s, user.id)})


@snipsels_bp.delete("/collections/<collection_id>/snipsels/<snipsel_id>")
@require_auth
def delete_from_collection(collection_id: str, snipsel_id: str):
    user = current_user()
    if not can_write_collection(user.id, collection_id):
        raise api_error(404, "not_found", "Collection not found")

    s = db.session.get(Snipsel, snipsel_id)
    if not s or s.deleted_at is not None:
        raise api_error(404, "not_found", "Snipsel not found")
    if s.owner_user_id != user.id and not can_read_snipsel_via_collections(
        user.id, snipsel_id
    ):
        raise api_error(404, "not_found", "Snipsel not found")

    cs = (
        db.session.execute(
            db.select(CollectionSnipsel).where(
                CollectionSnipsel.collection_id == collection_id,
                CollectionSnipsel.snipsel_id == snipsel_id,
            )
        )
        .scalars()
        .first()
    )
    if not cs:
        raise api_error(404, "not_found", "Snipsel not in collection")

    db.session.delete(cs)

    remaining = (
        db.session.execute(
            db.select(db.func.count())
            .select_from(CollectionSnipsel)
            .where(CollectionSnipsel.snipsel_id == snipsel_id)
        ).scalar()
        or 0
    )
    if remaining == 0 and s.owner_user_id == user.id:
        if _is_empty_snipsel(s):
            _hard_delete_snipsel(s)
        elif s.deleted_at is None:
            s.deleted_at = datetime.utcnow()
            s.deleted_by_id = user.id

    db.session.execute(
        db.update(Collection)
        .where(Collection.id == collection_id, Collection.deleted_at.is_(None))
        .values(modified_at=datetime.utcnow(), modified_by_id=user.id)
    )
    clear_search_cache(user.id)
    db.session.commit()
    # Notify: snipsel removed from collection
    sse_bus.publish(
        _snipsel_collection_user_ids(collection_id),
        {"type": "snipsels_updated", "collection_id": collection_id, "ids": [snipsel_id]},
        origin_client_id=request.headers.get("X-Client-Id"),
    )
    return json_response({"ok": True})


@snipsels_bp.patch("/collections/<collection_id>/snipsels/reorder")
@require_auth
@enforce_json
def reorder_collection(collection_id: str):
    user = current_user()
    if not can_write_collection(user.id, collection_id):
        raise api_error(404, "not_found", "Collection not found")
    data = request.get_json() or {}
    items = data.get("items")
    if not isinstance(items, list):
        raise api_error(400, "invalid_input", "items must be a list")

    for item in items:
        if not isinstance(item, dict):
            continue
        snipsel_id = item.get("snipsel_id")
        position = item.get("position")
        indent = item.get("indent")
        if not snipsel_id:
            continue

        s = db.session.get(Snipsel, snipsel_id)
        if not s or s.deleted_at is not None:
            continue
        if s.owner_user_id != user.id and not can_read_snipsel_via_collections(
            user.id, snipsel_id
        ):
            continue

        cs = (
            db.session.execute(
                db.select(CollectionSnipsel).where(
                    CollectionSnipsel.collection_id == collection_id,
                    CollectionSnipsel.snipsel_id == snipsel_id,
                )
            )
            .scalars()
            .first()
        )
        if not cs:
            continue

        if isinstance(position, int):
            cs.position = position
        if isinstance(indent, int) and indent >= 0:
            cs.indent = indent

    db.session.execute(
        db.update(Collection)
        .where(Collection.id == collection_id, Collection.deleted_at.is_(None))
        .values(modified_at=datetime.utcnow(), modified_by_id=user.id)
    )
    db.session.commit()
    # Notify: order changed in collection
    sse_bus.publish(
        _snipsel_collection_user_ids(collection_id),
        {"type": "snipsels_updated", "collection_id": collection_id, "ids": []},
        origin_client_id=request.headers.get("X-Client-Id"),
    )
    return json_response({"ok": True})


@snipsels_bp.delete("/collections/<collection_id>/snipsels/completed")
@require_auth
def delete_completed_tasks(collection_id: str):
    user = current_user()
    if not can_write_collection(user.id, collection_id):
        raise api_error(404, "not_found", "Collection not found")

    # Find all CollectionSnipsel entries for completed tasks in this collection
    stmt = (
        db.select(CollectionSnipsel)
        .join(Snipsel, Snipsel.id == CollectionSnipsel.snipsel_id)
        .where(
            CollectionSnipsel.collection_id == collection_id,
            Snipsel.task_done.in_([1, 2]),
            Snipsel.deleted_at.is_(None),
        )
    )
    items = db.session.execute(stmt).scalars().all()

    deleted_count = 0
    now = datetime.utcnow()

    for cs in items:
        snipsel_id = cs.snipsel_id
        s = cs.snipsel

        # Remove from this collection
        db.session.delete(cs)

        # Check if it should be fully deleted (last reference and owned by user)
        remaining = (
            db.session.execute(
                db.select(db.func.count())
                .select_from(CollectionSnipsel)
                .where(
                    CollectionSnipsel.snipsel_id == snipsel_id,
                    CollectionSnipsel.collection_id != collection_id,
                )
            ).scalar()
            or 0
        )

        if remaining == 0 and s.owner_user_id == user.id:
            if _is_empty_snipsel(s):
                _hard_delete_snipsel(s)
            else:
                s.deleted_at = now
                s.deleted_by_id = user.id

        deleted_count += 1

    if deleted_count > 0:
        db.session.execute(
            db.update(Collection)
            .where(Collection.id == collection_id)
            .values(modified_at=now, modified_by_id=user.id)
        )
        db.session.commit()

    return json_response({"ok": True, "count": deleted_count})


@snipsels_bp.post("/collections/<collection_id>/snipsels/completed/reset")
@require_auth
def reset_completed_tasks(collection_id: str):
    user = current_user()
    if not can_write_collection(user.id, collection_id):
        raise api_error(404, "not_found", "Collection not found")

    # Find all Snipsel IDs in this collection that are marked as done
    stmt = (
        db.select(Snipsel)
        .join(CollectionSnipsel, CollectionSnipsel.snipsel_id == Snipsel.id)
        .where(
            CollectionSnipsel.collection_id == collection_id,
            Snipsel.task_done.in_([1, 2]),
            Snipsel.deleted_at.is_(None),
        )
    )
    snipsels = db.session.execute(stmt).scalars().all()

    reset_count = 0
    now = datetime.utcnow()

    for s in snipsels:
        s.task_done = 0
        s.done_at = None
        s.done_by_id = None
        s.modified_at = now
        s.modified_by_id = user.id
        reset_count += 1

    if reset_count > 0:
        db.session.execute(
            db.update(Collection)
            .where(Collection.id == collection_id)
            .values(modified_at=now, modified_by_id=user.id)
        )
        db.session.commit()

    return json_response({"ok": True, "count": reset_count})


def _get_owned_snipsel(user_id: str, snipsel_id: str) -> Snipsel:
    s = db.session.get(Snipsel, snipsel_id)
    if not s or s.deleted_at is not None or s.owner_user_id != user_id:
        raise api_error(404, "not_found", "Snipsel not found")
    return s


def _sync_tags_mentions(
    *, user_id: str, snipsel: Snipsel, newly_became_task: bool = False
) -> None:
    text = snipsel.content_markdown or ""
    tag_names = extract_tags(text)
    mention_names = extract_mentions(text)

    old_mention_names = set(
        db.session.execute(
            db.select(Mention.name)
            .join(SnipselMention, SnipselMention.mention_id == Mention.id)
            .where(SnipselMention.snipsel_id == snipsel.id)
        )
        .scalars()
        .all()
    )
    existing_tags = (
        db.session.execute(
            db.select(Tag).where(Tag.owner_user_id == user_id, Tag.name.in_(tag_names))
        )
        .scalars()
        .all()
        if tag_names
        else []
    )
    by_name = {t.name: t for t in existing_tags}
    for name in tag_names:
        if name not in by_name:
            t = Tag(owner_user_id=user_id, name=name)
            db.session.add(t)
            db.session.flush()
            by_name[name] = t

    db.session.execute(db.delete(SnipselTag).where(SnipselTag.snipsel_id == snipsel.id))
    for t in by_name.values():
        db.session.add(SnipselTag(snipsel_id=snipsel.id, tag_id=t.id))

    existing_mentions = (
        db.session.execute(
            db.select(Mention).where(
                Mention.owner_user_id == user_id, Mention.name.in_(mention_names)
            )
        )
        .scalars()
        .all()
        if mention_names
        else []
    )
    m_by_name = {m.name: m for m in existing_mentions}
    for name in mention_names:
        if name not in m_by_name:
            m = Mention(owner_user_id=user_id, name=name)
            db.session.add(m)
            db.session.flush()
            m_by_name[name] = m

    db.session.execute(
        db.delete(SnipselMention).where(SnipselMention.snipsel_id == snipsel.id)
    )
    for m in m_by_name.values():
        db.session.add(SnipselMention(snipsel_id=snipsel.id, mention_id=m.id))

    # Check if this snipsel is in an active daily collection
    mention_day = db.session.execute(
        db.select(Collection.list_for_day)
        .join(CollectionSnipsel, Collection.id == CollectionSnipsel.collection_id)
        .where(
            CollectionSnipsel.snipsel_id == snipsel.id,
            Collection.list_for_day.is_not(None),
            Collection.deleted_at.is_(None),
        )
    ).scalars().first()
    is_in_daily = mention_day is not None

    for name in set(mention_names):
        if name not in old_mention_names or newly_became_task:
            mentioned_user = db.session.execute(
                db.select(User).where(User.username == name)
            ).scalar_one_or_none()
            if mentioned_user and mentioned_user.id != user_id:
                # Notifications are sent if:
                # 1. It's a task (assignment)
                # 2. It's in a daily collection (the system shares these mentions by default)
                # 3. The user already has collection access
                can_see = is_in_daily or can_read_snipsel_via_collections(
                    mentioned_user.id, snipsel.id
                )
                if snipsel.type == "task" or can_see:
                    author = db.session.get(User, user_id)
                    author_name = author.username if author else "Someone"
                    if snipsel.type == "task":
                        task_first = _get_task_preview(snipsel.content_markdown or "")
                        msg = (
                            f"{author_name} assigned a task to you: {task_first}"
                            if task_first
                            else f"{author_name} assigned a task to you."
                        )
                    else:
                        preview = _get_task_preview(snipsel.content_markdown or "")
                        msg = (
                            f"{author_name} mentioned you: {preview}"
                            if preview
                            else f"{author_name} mentioned you."
                        )
                    
                    notification_collection_id = None
                    if is_in_daily:
                        from snipsel_api.routes_collections import _get_or_create_daily_collection
                        dest_col = _get_or_create_daily_collection(mentioned_user.id, mention_day)
                        notification_collection_id = dest_col.id

                    if not _is_snipsel_muted(snipsel.id):
                        n = Notification(
                            user_id=mentioned_user.id,
                            message=msg,
                            snipsel_id=snipsel.id,
                            collection_id=notification_collection_id,
                        )
                        db.session.add(n)

    # Sync collection refs ([[Collection Title]] wiki-links)
    ref_titles = extract_collection_refs(text)
    db.session.execute(
        db.delete(SnipselCollectionRef).where(
            SnipselCollectionRef.snipsel_id == snipsel.id
        )
    )
    for title in ref_titles:
        # Look up accessible collections by title (case-insensitive)
        matched = (
            db.session.execute(
                db.select(Collection)
                .outerjoin(
                    CollectionShare,
                    db.and_(
                        CollectionShare.collection_id == Collection.id,
                        CollectionShare.shared_with_user_id == user_id,
                    ),
                )
                .where(
                    Collection.deleted_at.is_(None),
                    db.or_(
                        Collection.owner_user_id == user_id,
                        CollectionShare.permission.in_(["read", "write"]),
                    ),
                    db.func.lower(Collection.title) == title.lower(),
                )
                .limit(1)
            )
            .scalars()
            .first()
        )
        if matched:
            db.session.add(
                SnipselCollectionRef(snipsel_id=snipsel.id, collection_id=matched.id)
            )


def _get_task_preview(content_markdown: str) -> str:
    if not content_markdown:
        return ""
    lines = content_markdown.splitlines()
    first_line = lines[0].strip() if lines else ""
    # Remove @mention tokens (e.g. @daniel) so they don't appear redundantly
    first_line = re.sub(r"@\w+\s*", "", first_line).strip()
    if len(first_line) > 80:
        first_line = first_line[:80] + "..."
    elif len(lines) > 1:
        first_line = first_line + "..."
    return first_line


def _sync_backlinks(*, user_id: str, snipsel: Snipsel) -> None:
    db.session.execute(
        db.delete(SnipselLink).where(SnipselLink.from_snipsel_id == snipsel.id)
    )

    target_id = snipsel.internal_target_snipsel_id
    if not target_id:
        return

    target = db.session.get(Snipsel, target_id)
    if not target or target.owner_user_id != user_id or target.deleted_at is not None:
        return

    db.session.add(SnipselLink(from_snipsel_id=snipsel.id, to_snipsel_id=target_id))


def _is_snipsel_muted(snipsel_id: str) -> bool:
    """Returns True if the snipsel is in at least one collection and ALL such collections have mute_notifications=True."""
    # Find all collections this snipsel is in
    collection_ids = (
        db.session.execute(
            db.select(CollectionSnipsel.collection_id).where(
                CollectionSnipsel.snipsel_id == snipsel_id
            )
        )
        .scalars()
        .all()
    )
    if not collection_ids:
        return False

    # Check if any collection has notifications enabled
    not_muted_count = (
        db.session.execute(
            db.select(db.func.count())
            .select_from(Collection)
            .where(
                Collection.id.in_(collection_ids),
                Collection.deleted_at.is_(None),
                Collection.mute_notifications == False,
            )
        ).scalar()
        or 0
    )
    # If there is at least one collection that is NOT muted, then it's not muted overall.
    return not_muted_count == 0


def _snipsel_json(s: Snipsel, user_id: str | None = None) -> dict:
    from sqlalchemy.orm import joinedload
    refs = (
        db.session.execute(
            db.select(SnipselCollectionRef)
            .join(Collection, Collection.id == SnipselCollectionRef.collection_id)
            .options(joinedload(SnipselCollectionRef.collection))
            .where(
                SnipselCollectionRef.snipsel_id == s.id,
                Collection.deleted_at.is_(None),
            )
        )
        .scalars()
        .all()
    )

    return {
        "id": s.id,
        "type": s.type,
        "card_view": s.card_view,
        "content_markdown": s.content_markdown,
        "task_done": s.task_done,
        "done_at": s.done_at.isoformat() + "Z" if s.done_at else None,
        "done_by_id": s.done_by_id,
        "done_by_username": s.done_by.username if s.done_by else None,
        "external_url": s.external_url,
        "external_label": s.external_label,
        "internal_target_snipsel_id": s.internal_target_snipsel_id,
        "geo_lat": s.geo_lat,
        "geo_lng": s.geo_lng,
        "geo_accuracy_m": s.geo_accuracy_m,
        "reminder_at": s.reminder_at.isoformat() + "Z" if s.reminder_at else None,
        "reminder_rrule": s.reminder_rrule,
        "created_at": s.created_at.isoformat() + "Z",
        "created_by_id": s.created_by_id,
        "created_by_username": s.created_by.username if s.created_by else None,
        "modified_at": s.modified_at.isoformat() + "Z",
        "modified_by_id": s.modified_by_id,
        "modified_by_username": s.modified_by.username if s.modified_by else None,
        "reactions": s.get_reaction_summary(user_id) if user_id else [],
        "attachments": [
            {
                "id": a.id,
                "filename": a.filename,
                "mime_type": a.mime_type,
                "size_bytes": a.size_bytes,
                "has_thumbnail": a.thumbnail_path is not None,
            }
            for a in s.attachments
        ],
        "collection_refs": [
            {"title": r.collection.title, "collection_id": r.collection_id}
            for r in refs
        ],
    }


def _collection_item_json(
    cs: CollectionSnipsel,
    user_id: str | None = None,
    refs: list[SnipselCollectionRef] | None = None,
) -> dict:
    if refs is None:
        refs = (
            db.session.execute(
                db.select(SnipselCollectionRef)
                .join(Collection, Collection.id == SnipselCollectionRef.collection_id)
                .options(joinedload(SnipselCollectionRef.collection))
                .where(
                    SnipselCollectionRef.snipsel_id == cs.snipsel_id,
                    Collection.deleted_at.is_(None),
                )
            )
            .scalars()
            .all()
        )
    return {
        "collection_id": cs.collection_id,
        "snipsel_id": cs.snipsel_id,
        "position": cs.position,
        "indent": cs.indent,
        "snipsel": _snipsel_json(cs.snipsel, user_id),
        "collection_refs": [
            {"title": r.collection.title, "collection_id": r.collection_id}
            for r in refs
        ],
    }


@snipsels_bp.get("/snipsels/trash")
@require_auth
def list_trash_snipsels():
    user = current_user()
    stmt = (
        db.select(Snipsel)
        .options(
            joinedload(Snipsel.created_by),
            joinedload(Snipsel.modified_by),
            joinedload(Snipsel.done_by),
            selectinload(Snipsel.reactions),
            selectinload(Snipsel.attachments),
        )
        .where(Snipsel.owner_user_id == user.id, Snipsel.deleted_at.is_not(None))
        .order_by(Snipsel.deleted_at.desc())
    )
    items = db.session.execute(stmt).scalars().unique().all()

    out = []
    for s in items:
        j = _snipsel_json(s, user.id)
        j["deleted_at"] = s.deleted_at.isoformat() + "Z" if s.deleted_at else None
        out.append(j)

    return json_response({"snipsels": out})


@snipsels_bp.delete("/snipsels/trash")
@require_auth
def empty_trash_snipsels():
    user = current_user()
    stmt = db.select(Snipsel).where(
        Snipsel.owner_user_id == user.id, Snipsel.deleted_at.is_not(None)
    )
    snipsels = db.session.execute(stmt).scalars().all()

    from snipsel_api.models import (
        CollectionSnipsel,
        SnipselCollectionRef,
        SnipselLink,
        SnipselTag,
        SnipselMention,
        SnipselReaction,
        Notification,
    )
    from snipsel_api.routes_attachments import delete_attachment_file

    deleted_count = 0
    for s in snipsels:
        for att in s.attachments:
            delete_attachment_file(att)
            # Attachment rows will be deleted by SQLAlchemy cascade on snipsel

        # Manually clear relationships without cascade
        db.session.execute(
            db.delete(CollectionSnipsel).where(CollectionSnipsel.snipsel_id == s.id)
        )
        db.session.execute(
            db.delete(SnipselCollectionRef).where(
                SnipselCollectionRef.snipsel_id == s.id
            )
        )
        db.session.execute(
            db.delete(SnipselLink).where(
                db.or_(
                    SnipselLink.from_snipsel_id == s.id,
                    SnipselLink.to_snipsel_id == s.id,
                )
            )
        )
        db.session.execute(db.delete(SnipselTag).where(SnipselTag.snipsel_id == s.id))
        db.session.execute(
            db.delete(SnipselMention).where(SnipselMention.snipsel_id == s.id)
        )
        db.session.execute(
            db.delete(SnipselReaction).where(SnipselReaction.snipsel_id == s.id)
        )
        db.session.execute(
            db.delete(Notification).where(Notification.snipsel_id == s.id)
        )

        db.session.delete(s)
        deleted_count += 1

    db.session.commit()
    return json_response({"ok": True, "deleted": deleted_count})


@snipsels_bp.post("/snipsels/<snipsel_id>/restore")
@require_auth
@enforce_json
def restore_snipsel(snipsel_id: str):
    user = current_user()
    s = db.session.get(Snipsel, snipsel_id)
    if not s or s.owner_user_id != user.id:
        raise api_error(404, "not_found", "Snipsel not found")

    data = request.get_json() or {}
    collection_id = data.get("collection_id")

    if s.deleted_at is not None:
        s.deleted_at = None
        s.deleted_by_id = None
        s.modified_at = datetime.utcnow()
        s.modified_by_id = user.id

    if collection_id:
        if not can_write_collection(user.id, collection_id):
            raise api_error(404, "not_found", "Target collection not found")

        # Check if it's already in the collection
        exists = (
            db.session.execute(
                db.select(CollectionSnipsel).where(
                    CollectionSnipsel.collection_id == collection_id,
                    CollectionSnipsel.snipsel_id == snipsel_id,
                )
            )
            .scalars()
            .first()
        )

        if not exists:
            max_pos = (
                db.session.execute(
                    db.select(db.func.max(CollectionSnipsel.position)).where(
                        CollectionSnipsel.collection_id == collection_id
                    )
                ).scalar()
                or 0
            )
            cs = CollectionSnipsel(
                collection_id=collection_id,
                snipsel_id=s.id,
                position=max_pos + 1,
                indent=0,
            )
            db.session.add(cs)

            db.session.execute(
                db.update(Collection)
                .where(Collection.id == collection_id, Collection.deleted_at.is_(None))
                .values(modified_at=datetime.utcnow(), modified_by_id=user.id)
            )

    db.session.commit()
    return json_response({"snipsel": _snipsel_json(s, user.id)})


@snipsels_bp.delete("/snipsels/trash/<snipsel_id>")
@require_auth
def permanent_delete_snipsel(snipsel_id: str):
    user = current_user()
    s = db.session.get(Snipsel, snipsel_id)
    if not s or s.owner_user_id != user.id:
        raise api_error(404, "not_found", "Snipsel not found")

    if s.deleted_at is None:
        raise api_error(400, "invalid_state", "Snipsel is not in the trash")

    from snipsel_api.models import (
        CollectionSnipsel,
        SnipselCollectionRef,
        SnipselLink,
        SnipselTag,
        SnipselMention,
        SnipselReaction,
        Notification,
    )
    from snipsel_api.routes_attachments import delete_attachment_file

    for att in s.attachments:
        delete_attachment_file(att)

    # Manually clear relationships without cascade
    db.session.execute(
        db.delete(CollectionSnipsel).where(CollectionSnipsel.snipsel_id == s.id)
    )
    db.session.execute(
        db.delete(SnipselCollectionRef).where(SnipselCollectionRef.snipsel_id == s.id)
    )
    db.session.execute(
        db.delete(SnipselLink).where(
            db.or_(
                SnipselLink.from_snipsel_id == s.id, SnipselLink.to_snipsel_id == s.id
            )
        )
    )
    db.session.execute(db.delete(SnipselTag).where(SnipselTag.snipsel_id == s.id))
    db.session.execute(
        db.delete(SnipselMention).where(SnipselMention.snipsel_id == s.id)
    )
    db.session.execute(
        db.delete(SnipselReaction).where(SnipselReaction.snipsel_id == s.id)
    )
    db.session.execute(db.delete(Notification).where(Notification.snipsel_id == s.id))

    db.session.delete(s)
    db.session.commit()

    return json_response({"ok": True, "deleted": 1})


@snipsels_bp.post("/snipsels/<snipsel_id>/diced/ban")
@require_auth
def ban_from_diced_moments(snipsel_id: str):
    user = current_user()
    s = _get_owned_snipsel(user.id, snipsel_id)
    s.diced_count = -1
    db.session.commit()
    return json_response({"ok": True})
