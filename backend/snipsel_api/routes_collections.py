from __future__ import annotations

from sqlalchemy import extract

import logging
import uuid
from datetime import date, datetime, timedelta

from flask import Blueprint, request

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload

logger = logging.getLogger(__name__)

from snipsel_api.auth_session import (
    current_user,
    enforce_json,
    json_response,
    require_auth,
)
from snipsel_api.errors import api_error
from snipsel_api.extensions import db
from snipsel_api.models import (
    Attachment,
    Collection,
    CollectionFavorite,
    CollectionShare,
    CollectionSnipsel,
    Snipsel,
    User,
    Notification,
    SnipselCollectionRef,
    CollectionVisit,
    Tag,
    SnipselTag,
)
from snipsel_api.permissions import (
    can_read_collection,
    can_write_collection,
    get_collection_access_level,
    is_passcode_unlocked,
)
from snipsel_api.routes_attachments import (
    _resolve_attachment_path,
    _resolve_thumbnail_path,
)
from snipsel_api.routes_snipsels import _sync_backlinks, _sync_tags_mentions, _collection_item_json
from snipsel_api import sse_bus

collections_bp = Blueprint("collections", __name__)


def _collection_user_ids(collection: Collection) -> list[str]:
    """Return IDs of all users who have access to *collection* (owner + shares)."""
    ids = [collection.owner_user_id]
    share_user_ids = (
        db.session.execute(
            db.select(CollectionShare.shared_with_user_id).where(
                CollectionShare.collection_id == collection.id
            )
        )
        .scalars()
        .all()
    )
    ids.extend(share_user_ids)
    return ids


def _get_share_permission(user_id: str, collection_id: str) -> str | None:
    level = get_collection_access_level(user_id, collection_id)
    if level in {"owner", "write", "read"}:
        return "write" if level == "write" else ("read" if level == "read" else None)
    return None


@collections_bp.get("")
@require_auth
def list_collections():
    user = current_user()
    include_archived = request.args.get("include_archived") == "1"
    owned_ids = db.select(Collection.id).where(
        Collection.owner_user_id == user.id, Collection.deleted_at.is_(None)
    )
    if not include_archived:
        owned_ids = owned_ids.where(Collection.archived_at.is_(None))

    shared_ids = (
        db.select(Collection.id)
        .join(CollectionShare, CollectionShare.collection_id == Collection.id)
        .where(
            Collection.deleted_at.is_(None),
            CollectionShare.shared_with_user_id == user.id,
        )
    )
    if not include_archived:
        shared_ids = shared_ids.where(Collection.archived_at.is_(None))

    ids_subq = owned_ids.union(shared_ids).subquery()
    ids_select = db.select(ids_subq.c.id)

    q = db.select(Collection).where(
        Collection.id.in_(ids_select), Collection.deleted_at.is_(None)
    )
    if not include_archived:
        q = q.where(Collection.archived_at.is_(None))
    q = q.order_by(
        Collection.list_for_day.desc().nullslast(), Collection.created_at.desc()
    )
    items = db.session.execute(q).scalars().all()

    shared_collection_ids = [c.id for c in items if c.owner_user_id != user.id]
    perms = {
        cid: perm
        for cid, perm in (
            db.session.execute(
                db.select(
                    CollectionShare.collection_id, CollectionShare.permission
                ).where(
                    CollectionShare.shared_with_user_id == user.id,
                    CollectionShare.collection_id.in_(shared_collection_ids)
                    if shared_collection_ids
                    else db.false(),
                )
            ).all()
        )
    }
    owner_ids = list({c.owner_user_id for c in items if c.owner_user_id != user.id})
    owner_names = {
        uid: uname
        for uid, uname in (
            db.session.execute(
                db.select(User.id, User.username).where(User.id.in_(owner_ids))
            ).all()
            if owner_ids
            else []
        )
    }

    owned_item_ids = [c.id for c in items if c.owner_user_id == user.id]
    shared_out_ids = set(
        db.session.execute(
            db.select(db.distinct(CollectionShare.collection_id)).where(
                CollectionShare.collection_id.in_(owned_item_ids)
                if owned_item_ids
                else db.false()
            )
        )
        .scalars()
        .all()
    )

    fav_ids = set(
        db.session.execute(
            db.select(CollectionFavorite.collection_id).where(
                CollectionFavorite.user_id == user.id
            )
        )
        .scalars()
        .all()
    )

    out = []
    for c in items:
        j = _collection_json(c)
        j["is_favorite"] = c.id in fav_ids
        if c.owner_user_id == user.id:
            j["access_level"] = "owner"
            j["shared_out"] = c.id in shared_out_ids
        else:
            perm = perms.get(c.id)
            j["access_level"] = "write" if perm == "write" else "read"
            j["shared_by_username"] = owner_names.get(c.owner_user_id)
            j["shared_out"] = False
        out.append(j)

    return json_response({"collections": out})


@collections_bp.get("/sync/all")
@require_auth
def sync_all_data():
    user = current_user()
    
    # Get all collections (including archived for full offline sync)
    owned_ids = db.select(Collection.id).where(
        Collection.owner_user_id == user.id, Collection.deleted_at.is_(None)
    )
    shared_ids = (
        db.select(Collection.id)
        .join(CollectionShare, CollectionShare.collection_id == Collection.id)
        .where(
            Collection.deleted_at.is_(None),
            CollectionShare.shared_with_user_id == user.id,
        )
    )
    ids_subq = owned_ids.union(shared_ids).subquery()
    ids_select = db.select(ids_subq.c.id)

    q = db.select(Collection).where(
        Collection.id.in_(ids_select), Collection.deleted_at.is_(None)
    )
    collections = db.session.execute(q).scalars().all()

    # Favorites
    fav_ids = set(
        db.session.execute(
            db.select(CollectionFavorite.collection_id).where(
                CollectionFavorite.user_id == user.id
            )
        )
        .scalars()
        .all()
    )

    # Sharing info
    shared_collection_ids = [c.id for c in collections if c.owner_user_id != user.id]
    perms = {
        cid: perm
        for cid, perm in (
            db.session.execute(
                db.select(
                    CollectionShare.collection_id, CollectionShare.permission
                ).where(
                    CollectionShare.shared_with_user_id == user.id,
                    CollectionShare.collection_id.in_(shared_collection_ids)
                    if shared_collection_ids
                    else db.false(),
                )
            ).all()
        )
    }
    owner_ids = list({c.owner_user_id for c in collections if c.owner_user_id != user.id})
    owner_names = {
        uid: uname
        for uid, uname in (
            db.session.execute(
                db.select(User.id, User.username).where(User.id.in_(owner_ids))
            ).all()
            if owner_ids
            else []
        )
    }

    owned_item_ids = [c.id for c in collections if c.owner_user_id == user.id]
    shared_out_ids = set(
        db.session.execute(
            db.select(db.distinct(CollectionShare.collection_id)).where(
                CollectionShare.collection_id.in_(owned_item_ids)
                if owned_item_ids
                else db.false()
            )
        )
        .scalars()
        .all()
    )

    cols_out = []
    for c in collections:
        j = _collection_json(c)
        j["is_favorite"] = c.id in fav_ids
        if c.owner_user_id == user.id:
            j["access_level"] = "owner"
            j["shared_out"] = c.id in shared_out_ids
        else:
            perm = perms.get(c.id)
            j["access_level"] = "write" if perm == "write" else "read"
            j["shared_by_username"] = owner_names.get(c.owner_user_id)
            j["shared_out"] = False
        cols_out.append(j)

    # Get all items for all collections
    all_collection_id_list = [c.id for c in collections]
    items_stmt = (
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
            CollectionSnipsel.collection_id.in_(all_collection_id_list) if all_collection_id_list else db.false(),
            Snipsel.deleted_at.is_(None),
        )
        .order_by(CollectionSnipsel.position.asc())
    )
    all_items = db.session.execute(items_stmt).scalars().unique().all()
    
    # Pre-fetch collection refs for efficiency
    snipsel_ids = list({cs.snipsel_id for cs in all_items})
    refs_by_snipsel_id = {sid: [] for sid in snipsel_ids}
    if snipsel_ids:
        all_refs_stmt = (
            db.select(SnipselCollectionRef)
            .join(Collection, Collection.id == SnipselCollectionRef.collection_id)
            .options(joinedload(SnipselCollectionRef.collection))
            .where(
                SnipselCollectionRef.snipsel_id.in_(snipsel_ids),
                Collection.deleted_at.is_(None),
            )
        )
        all_refs = db.session.execute(all_refs_stmt).scalars().all()
        for r in all_refs:
            refs_by_snipsel_id[r.snipsel_id].append(r)

    items_out = {}
    for cs in all_items:
        if cs.collection_id not in items_out:
            items_out[cs.collection_id] = []
        items_out[cs.collection_id].append(
            _collection_item_json(cs, user.id, refs_by_snipsel_id[cs.snipsel_id])
        )

    return json_response({
        "collections": cols_out,
        "items": items_out
    })


@collections_bp.get("/today")
@require_auth
def get_today_collection():
    user = current_user()
    day_str = request.args.get("day")
    day = date.fromisoformat(day_str) if day_str else date.today()

    c = _get_or_create_daily_collection(user_id=user.id, day=day)

    j = _collection_json(c)
    j["is_favorite"] = (
        db.session.execute(
            db.select(CollectionFavorite).where(
                CollectionFavorite.user_id == user.id,
                CollectionFavorite.collection_id == c.id,
            )
        )
        .scalars()
        .first()
        is not None
    )
    j["access_level"] = "owner"
    
    # Commit changes from helper if any (creation, carry-overs)
    db.session.commit()
    
    return json_response({"collection": j})


@collections_bp.get("/throwback")
@require_auth
def get_throwback_collections():
    user = current_user()
    day_str = request.args.get("day")
    if not day_str:
        raise api_error(400, "invalid_input", "day parameter is required")
    try:
        target_day = date.fromisoformat(day_str)
    except ValueError:
        raise api_error(400, "invalid_input", "day must be in YYYY-MM-DD format")

    q = (
        db.select(Collection)
        .where(
            Collection.owner_user_id == user.id,
            Collection.list_for_day.is_not(None),
            extract("month", Collection.list_for_day) == target_day.month,
            extract("day", Collection.list_for_day) == target_day.day,
            Collection.list_for_day != target_day,
            Collection.deleted_at.is_(None),
        )
        .order_by(Collection.list_for_day.asc())
    )

    items = db.session.execute(q).scalars().all()
    out = []
    for c in items:
        out.append(
            {
                "id": c.id,
                "year": c.list_for_day.year,
                "title": c.title,
                "icon": c.icon,
            }
        )
    return json_response({"collections": out})


@collections_bp.get("/diced_moment")
@require_auth
def get_diced_moment():
    user = current_user()
    if not user.diced_moments_tags:
        return json_response({"snipsel": None})

    tag_names = [
        t.strip().lower().lstrip("#") for t in user.diced_moments_tags.split(",") if t.strip()
    ]
    if not tag_names:
        return json_response({"snipsel": None})

    from sqlalchemy.sql import func

    q = (
        db.select(Snipsel)
        .options(
            joinedload(Snipsel.created_by),
            joinedload(Snipsel.modified_by),
            joinedload(Snipsel.done_by),
            selectinload(Snipsel.reactions),
            selectinload(Snipsel.attachments),
        )
        .join(SnipselTag, Snipsel.id == SnipselTag.snipsel_id)
        .join(Tag, Tag.id == SnipselTag.tag_id)
        .where(
            Snipsel.owner_user_id == user.id,
            Snipsel.deleted_at.is_(None),
            Snipsel.diced_count >= 0,
            func.lower(Tag.name).in_(tag_names),
        )
        .order_by(Snipsel.diced_count.asc(), func.random())
        .limit(1)
    )

    snipsel = db.session.execute(q).scalars().unique().first()
    if not snipsel:
        return json_response({"snipsel": None})

    snipsel.diced_count += 1
    db.session.commit()

    from snipsel_api.routes_snipsels import _snipsel_json

    return json_response({"snipsel": _snipsel_json(snipsel, user.id)})


def _get_or_create_daily_collection(user_id: str, day: date) -> Collection:
    """Finds or creates a daily collection for a user. Refactored from get_today_collection."""
    user = db.session.get(User, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    existing = (
        db.session.execute(
            db.select(Collection).where(
                Collection.owner_user_id == user_id,
                Collection.list_for_day == day,
                Collection.deleted_at.is_(None),
            )
        )
        .scalars()
        .first()
    )
    if existing:
        _maybe_carry_over_open_tasks(user=user, today_collection=existing, day=day)
        return existing

    conflict_deleted = (
        db.session.execute(
            db.select(Collection).where(
                Collection.owner_user_id == user_id,
                Collection.list_for_day == day,
                Collection.deleted_at.is_not(None),
            )
        )
        .scalars()
        .first()
    )
    if conflict_deleted:
        conflict_deleted.list_for_day = None
        db.session.flush()

    c = Collection(
        owner_user_id=user_id,
        title=day.isoformat(),
        icon="📅",
        list_for_day=day,
        created_by_id=user_id,
        modified_by_id=user_id,
    )

    tpl_id = getattr(user, "day_collection_template_id", None)
    if tpl_id:
        tpl = db.session.get(Collection, tpl_id)
        if (
            tpl
            and tpl.deleted_at is None
            and tpl.owner_user_id == user_id
            and getattr(tpl, "is_template", False)
        ):
            c.icon = tpl.icon
            c.header_image_url = tpl.header_image_url
            c.header_color = tpl.header_color
            c.header_image_position = tpl.header_image_position
            c.header_image_x_position = tpl.header_image_x_position
            c.header_image_zoom = tpl.header_image_zoom
            c.show_completed_tasks = tpl.show_completed_tasks
            if tpl.default_snipsel_type:
                c.default_snipsel_type = tpl.default_snipsel_type
    db.session.add(c)
    db.session.flush()

    _maybe_carry_over_open_tasks(user=user, today_collection=c, day=day)

    if tpl_id:
        _maybe_copy_template_contents(
            user=user, template_collection_id=tpl_id, target_collection=c
        )
    
    return c


def _maybe_copy_template_contents(
    *, user: User, template_collection_id: str, target_collection: Collection
) -> None:
    max_pos = (
        db.session.execute(
            db.select(db.func.max(CollectionSnipsel.position)).where(
                CollectionSnipsel.collection_id == target_collection.id
            )
        ).scalar()
        or 0
    )
    _insert_template_into_collection(
        user=user,
        template_collection_id=template_collection_id,
        target_collection=target_collection,
        position_offset=max_pos,
    )


def _insert_template_into_collection(
    *,
    user: User,
    template_collection_id: str,
    target_collection: Collection,
    position_offset: int,
) -> None:
    tpl = db.session.get(Collection, template_collection_id)
    if (
        not tpl
        or tpl.deleted_at is not None
        or tpl.owner_user_id != user.id
        or not getattr(tpl, "is_template", False)
    ):
        return

    tpl_items = (
        db.session.execute(
            db.select(CollectionSnipsel)
            .join(Snipsel, Snipsel.id == CollectionSnipsel.snipsel_id)
            .where(
                CollectionSnipsel.collection_id == tpl.id, Snipsel.deleted_at.is_(None)
            )
            .order_by(CollectionSnipsel.position.asc())
        )
        .scalars()
        .all()
    )

    old_to_new: dict[str, str] = {}
    new_items: list[tuple[str, int, int]] = []

    for cs in tpl_items:
        src = cs.snipsel
        ns = Snipsel(
            owner_user_id=user.id,
            type=src.type,
            content_markdown=src.content_markdown,
            task_done=src.task_done,
            done_at=src.done_at,
            done_by_id=src.done_by_id,
            external_url=src.external_url,
            external_label=src.external_label,
            internal_target_snipsel_id=None,
            geo_lat=src.geo_lat,
            geo_lng=src.geo_lng,
            geo_accuracy_m=src.geo_accuracy_m,
            created_by_id=user.id,
            modified_by_id=user.id,
        )
        db.session.add(ns)
        db.session.flush()
        old_to_new[src.id] = ns.id
        new_items.append((ns.id, position_offset + cs.position, cs.indent))

        for a in src.attachments:
            src_path = _resolve_attachment_path(a)
            if not src_path:
                continue

            upload_dir = src_path.parent
            new_att_id = str(uuid.uuid4())
            dst_path = upload_dir / f"{new_att_id}_{a.filename}"
            try:
                dst_path.write_bytes(src_path.read_bytes())
            except OSError:
                continue

            thumb_path = None
            src_thumb = _resolve_thumbnail_path(a)
            if src_thumb:
                thumb_path = upload_dir / f"{new_att_id}_thumb.jpg"
                try:
                    thumb_path.write_bytes(src_thumb.read_bytes())
                except OSError:
                    thumb_path = None

            na = Attachment(
                id=new_att_id,
                snipsel_id=ns.id,
                filename=a.filename,
                mime_type=a.mime_type,
                size_bytes=int(dst_path.stat().st_size),
                storage_path=str(dst_path),
                thumbnail_path=str(thumb_path) if thumb_path else None,
                created_by_id=user.id,
            )
            db.session.add(na)

    for old_id, new_id in old_to_new.items():
        src = db.session.get(Snipsel, old_id)
        if not src or not src.internal_target_snipsel_id:
            continue
        mapped = old_to_new.get(src.internal_target_snipsel_id)
        if mapped:
            ns = db.session.get(Snipsel, new_id)
            if ns:
                ns.internal_target_snipsel_id = mapped

    for new_id in old_to_new.values():
        ns = db.session.get(Snipsel, new_id)
        if ns:
            _sync_tags_mentions(user_id=user.id, snipsel=ns)
            _sync_backlinks(user_id=user.id, snipsel=ns)

    for snipsel_id, pos, indent in new_items:
        db.session.add(
            CollectionSnipsel(
                collection_id=target_collection.id,
                snipsel_id=snipsel_id,
                position=pos,
                indent=indent,
            )
        )

    shares = (
        db.session.execute(
            db.select(CollectionShare).where(CollectionShare.collection_id == tpl.id)
        )
        .scalars()
        .all()
    )
    for s in shares:
        existing = (
            db.session.execute(
                db.select(CollectionShare).where(
                    CollectionShare.collection_id == target_collection.id,
                    CollectionShare.shared_with_user_id == s.shared_with_user_id,
                )
            )
            .scalars()
            .first()
        )
        if existing:
            existing.permission = s.permission
            continue
        db.session.add(
            CollectionShare(
                collection_id=target_collection.id,
                shared_with_user_id=s.shared_with_user_id,
                permission=s.permission,
                created_by_user_id=user.id,
            )
        )

        n = Notification(
            user_id=s.shared_with_user_id,
            message=f"{user.username} shared collection '{target_collection.title}' with you.",
            collection_id=target_collection.id,
        )
        db.session.add(n)
    db.session.commit()


@collections_bp.post("/<collection_id>/insert_template")
@require_auth
@enforce_json
def insert_template(collection_id: str):
    user = current_user()
    if not can_write_collection(user.id, collection_id):
        raise api_error(404, "not_found", "Collection not found")
    target = db.session.get(Collection, collection_id)
    if not target or target.deleted_at is not None:
        raise api_error(404, "not_found", "Collection not found")

    data = request.get_json() or {}
    template_collection_id = (data.get("template_collection_id") or "").strip()
    if not template_collection_id:
        raise api_error(400, "invalid_input", "template_collection_id is required")

    max_pos = (
        db.session.execute(
            db.select(db.func.max(CollectionSnipsel.position)).where(
                CollectionSnipsel.collection_id == target.id
            )
        ).scalar()
        or 0
    )
    _insert_template_into_collection(
        user=user,
        template_collection_id=template_collection_id,
        target_collection=target,
        position_offset=max_pos,
    )
    return json_response({"ok": True})


def _maybe_carry_over_open_tasks(user, today_collection: Collection, day: date) -> None:
    """Move open tasks from past day-collections into today's collection.

    Uses SELECT FOR UPDATE on the CollectionSnipsel rows to prevent two
    concurrent requests (e.g. two open browser tabs) from racing and
    producing a UniqueConstraint violation that would silently discard tasks.
    The entire mutation is wrapped in try/except so a failed commit always
    triggers a rollback and never leaves rows in an inconsistent state.
    """
    log_prefix = f"[CarryOver user={user.id} day={day} today_col={today_collection.id}]"

    # Guard: only carry over to today
    if day != date.today():
        logger.debug(
            "%s Skipping – requested day %s is not today (%s)",
            log_prefix,
            day,
            date.today(),
        )
        return
    if not getattr(user, "carry_over_open_tasks", True):
        logger.debug(
            "%s Skipping – carry_over_open_tasks is disabled for user", log_prefix
        )
        return

    start_day = day - timedelta(days=30)
    logger.debug(
        "%s Looking for past day-collections between %s and %s",
        log_prefix,
        start_day,
        day,
    )

    past_collections = (
        db.session.execute(
            db.select(Collection)
            .where(
                Collection.owner_user_id == user.id,
                Collection.deleted_at.is_(None),
                Collection.list_for_day.is_not(None),
                Collection.list_for_day >= start_day,
                Collection.list_for_day < day,
            )
            .order_by(Collection.list_for_day.desc())
        )
        .scalars()
        .all()
    )

    if not past_collections:
        logger.debug(
            "%s No past day-collections found – nothing to carry over", log_prefix
        )
        return

    logger.debug(
        "%s Found %d past day-collection(s): %s",
        log_prefix,
        len(past_collections),
        [(c.id, str(c.list_for_day)) for c in past_collections],
    )

    max_pos = (
        db.session.execute(
            db.select(db.func.max(CollectionSnipsel.position)).where(
                CollectionSnipsel.collection_id == today_collection.id
            )
        ).scalar()
        or 0
    )
    logger.debug(
        "%s Current max position in today's collection: %d", log_prefix, max_pos
    )

    moved_count = 0
    deleted_duplicate_count = 0

    try:
        for src in past_collections:
            # Lock the candidate rows for this source collection so that a
            # parallel request cannot modify them between our read and our
            # UPDATE, which would cause a UniqueConstraint violation on
            # (collection_id, snipsel_id) and silently drop tasks.
            items = (
                db.session.execute(
                    db.select(CollectionSnipsel)
                    .join(Snipsel, Snipsel.id == CollectionSnipsel.snipsel_id)
                    .where(
                        CollectionSnipsel.collection_id == src.id,
                        Snipsel.deleted_at.is_(None),
                        Snipsel.type == "task",
                        Snipsel.task_done == 0,
                    )
                    .order_by(CollectionSnipsel.position.asc())
                    .with_for_update(
                        skip_locked=True
                    )  # skip rows locked by a concurrent request
                )
                .scalars()
                .all()
            )

            logger.debug(
                "%s Source collection %s (%s): %d open task(s) found (after lock)",
                log_prefix,
                src.id,
                src.list_for_day,
                len(items),
            )

            for cs in items:
                snipsel_preview = ""
                try:
                    snipsel_preview = (cs.snipsel.content_markdown or "")[:60].replace(
                        "\n", " "
                    )
                except Exception:
                    pass

                # Check if this snipsel is already in today's collection
                already = (
                    db.session.execute(
                        db.select(CollectionSnipsel).where(
                            CollectionSnipsel.collection_id == today_collection.id,
                            CollectionSnipsel.snipsel_id == cs.snipsel_id,
                        )
                    )
                    .scalars()
                    .first()
                )
                if already:
                    logger.debug(
                        "%s  Snipsel %s already in today – removing duplicate src entry (cs.id=%s) | '%s'",
                        log_prefix,
                        cs.snipsel_id,
                        cs.id,
                        snipsel_preview,
                    )
                    db.session.delete(cs)
                    deleted_duplicate_count += 1
                    continue

                max_pos += 1
                old_collection_id = cs.collection_id
                cs.collection_id = today_collection.id
                cs.position = max_pos
                moved_count += 1
                logger.debug(
                    "%s  Moved snipsel %s from collection %s → %s (pos=%d) | '%s'",
                    log_prefix,
                    cs.snipsel_id,
                    old_collection_id,
                    today_collection.id,
                    max_pos,
                    snipsel_preview,
                )

        # ── Orphan recovery ────────────────────────────────────────────────────
        # Find open tasks owned by this user that are not linked to ANY
        # collection (no CollectionSnipsel row exists). This catches tasks that
        # lost their collection reference through previous bugs or unexpected
        # database states, and rescues them back onto today's list.
        orphaned_snipsels = (
            db.session.execute(
                db.select(Snipsel).where(
                    Snipsel.owner_user_id == user.id,
                    Snipsel.deleted_at.is_(None),
                    Snipsel.type == "task",
                    Snipsel.task_done == 0,
                    ~Snipsel.id.in_(db.select(CollectionSnipsel.snipsel_id)),
                )
            )
            .scalars()
            .all()
        )

        rescued_count = 0
        for orphan in orphaned_snipsels:
            orphan_preview = (orphan.content_markdown or "")[:60].replace("\n", " ")
            logger.warning(
                "%s  ORPHAN DETECTED – snipsel %s has no collection! Rescuing to today. | '%s'",
                log_prefix,
                orphan.id,
                orphan_preview,
            )
            max_pos += 1
            db.session.add(
                CollectionSnipsel(
                    collection_id=today_collection.id,
                    snipsel_id=orphan.id,
                    position=max_pos,
                    indent=0,
                )
            )
            rescued_count += 1

        if rescued_count > 0:
            logger.warning(
                "%s  %d orphaned task(s) rescued to today's collection.",
                log_prefix,
                rescued_count,
            )
            today_collection.modified_at = datetime.utcnow()
            today_collection.modified_by_id = user.id
        # ── End orphan recovery ────────────────────────────────────────────────

        logger.info(
            "%s Summary before commit: moved=%d, duplicates_removed=%d, orphans_rescued=%d",
            log_prefix,
            moved_count,
            deleted_duplicate_count,
            rescued_count,
        )

        if moved_count > 0:
            # Touch modified_at so frontend caches/lists refresh
            today_collection.modified_at = datetime.utcnow()
            today_collection.modified_by_id = user.id

        db.session.commit()
        logger.info(
            "%s Commit successful. %d task(s) carried over, %d duplicate(s) cleaned up, %d orphan(s) rescued.",
            log_prefix,
            moved_count,
            deleted_duplicate_count,
            rescued_count,
        )

    except Exception as exc:
        logger.error(
            "%s ERROR during carry-over – rolling back! Exception: %s",
            log_prefix,
            exc,
            exc_info=True,
        )
        db.session.rollback()
        # Do not re-raise: a carry-over failure should not break the
        # GET /today response. The tasks remain in their source collections
        # and will be picked up on the next request.


@collections_bp.post("")
@require_auth
@enforce_json
def create_collection():
    user = current_user()
    data = request.get_json() or {}

    title = (data.get("title") or "").strip()
    icon = (data.get("icon") or "🗒").strip() or "🗒"
    header_image_url = (data.get("header_image_url") or "").strip() or None
    header_color = (data.get("header_color") or "").strip() or None
    default_snipsel_type = (data.get("default_snipsel_type") or "").strip() or None
    show_completed_tasks = (
        data.get("show_completed_tasks") if "show_completed_tasks" in data else True
    )

    if not title:
        raise api_error(400, "invalid_input", "title is required")

    c = Collection(
        owner_user_id=user.id,
        title=title,
        icon=icon,
        header_image_url=header_image_url,
        header_color=header_color,
        default_snipsel_type=default_snipsel_type,
        show_completed_tasks=show_completed_tasks,
        mute_notifications=data.get("mute_notifications")
        if "mute_notifications" in data
        else False,
        created_by_id=user.id,
        modified_by_id=user.id,
    )
    db.session.add(c)
    db.session.commit()
    j = _collection_json(c)
    j["is_favorite"] = False
    j["access_level"] = "owner"
    # Notify all clients of the owner that the collection list changed
    sse_bus.publish([user.id], {"type": "collection_list_changed"},
                   origin_client_id=request.headers.get("X-Client-Id"))
    return json_response({"collection": j}, status=201)


@collections_bp.get("/<collection_id>")
@require_auth
def get_collection(collection_id: str):
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

    j = _collection_json(c)
    j["is_favorite"] = (
        db.session.execute(
            db.select(CollectionFavorite).where(
                CollectionFavorite.user_id == user.id,
                CollectionFavorite.collection_id == c.id,
            )
        )
        .scalars()
        .first()
        is not None
    )
    if c.owner_user_id == user.id:
        j["access_level"] = "owner"
    else:
        level = get_collection_access_level(user.id, c.id)
        j["access_level"] = "write" if level == "write" else "read"
        j["shared_by_username"] = (
            db.session.execute(
                db.select(User.username).where(User.id == c.owner_user_id)
            )
            .scalars()
            .first()
        )
    # Record visit
    visit = db.session.get(CollectionVisit, (user.id, c.id))
    if visit:
        visit.visited_at = datetime.utcnow()
    else:
        db.session.add(CollectionVisit(user_id=user.id, collection_id=c.id))
    db.session.commit()

    return json_response({"collection": j})


@collections_bp.patch("/<collection_id>")
@require_auth
@enforce_json
def update_collection(collection_id: str):
    user = current_user()
    c = _get_owned_collection(user.id, collection_id)
    data = request.get_json() or {}

    if "title" in data:
        title = (data.get("title") or "").strip()
        if not title:
            raise api_error(400, "invalid_input", "title cannot be empty")
        c.title = title
    if "icon" in data:
        icon = (data.get("icon") or "").strip()
        if not icon:
            raise api_error(400, "invalid_input", "icon cannot be empty")
        c.icon = icon
    if "header_image_url" in data:
        new_url = (data.get("header_image_url") or "").strip() or None
        if new_url != c.header_image_url:
            # If old one was an internal attachment, clean it up
            if c.header_image_url and c.header_image_url.startswith(
                "/api/attachments/"
            ):
                from snipsel_api.routes_attachments import (
                    delete_collection_header_attachments,
                )

                delete_collection_header_attachments(collection_id)
            c.header_image_url = new_url
    if "header_color" in data:
        c.header_color = (data.get("header_color") or "").strip() or None
    if "header_image_position" in data:
        c.header_image_position = (
            data.get("header_image_position") or ""
        ).strip() or "50%"
    if "header_image_x_position" in data:
        c.header_image_x_position = (
            data.get("header_image_x_position") or ""
        ).strip() or "50%"
    if "header_image_zoom" in data:
        try:
            c.header_image_zoom = float(data.get("header_image_zoom") or 1.0)
        except (ValueError, TypeError):
            c.header_image_zoom = 1.0
    if "archived" in data:
        archived = bool(data.get("archived"))
        c.archived_at = datetime.utcnow() if archived else None
    if "is_template" in data:
        c.is_template = bool(data.get("is_template"))
    if "is_passcode_protected" in data:
        c.is_passcode_protected = bool(data.get("is_passcode_protected"))
    if "default_snipsel_type" in data:
        c.default_snipsel_type = (
            data.get("default_snipsel_type") or ""
        ).strip() or None
    if "show_completed_tasks" in data:
        c.show_completed_tasks = bool(data.get("show_completed_tasks"))
    if "mute_notifications" in data:
        c.mute_notifications = bool(data.get("mute_notifications"))
    if "exclude_from_todo_list" in data:
        c.exclude_from_todo_list = bool(data.get("exclude_from_todo_list"))

    c.modified_by_id = user.id
    db.session.commit()
    j = _collection_json(c)
    j["is_favorite"] = (
        db.session.execute(
            db.select(CollectionFavorite).where(
                CollectionFavorite.user_id == user.id,
                CollectionFavorite.collection_id == c.id,
            )
        )
        .scalars()
        .first()
        is not None
    )
    j["access_level"] = "owner"
    # Notify all users with access that this collection changed
    sse_bus.publish(_collection_user_ids(c), {"type": "collection_updated", "ids": [c.id]},
                   origin_client_id=request.headers.get("X-Client-Id"))
    return json_response({"collection": j})


@collections_bp.delete("/<collection_id>")
@require_auth
def delete_collection(collection_id: str):
    user = current_user()
    c = _get_owned_collection(user.id, collection_id)
    from sqlalchemy import and_

    # Check for backlinks from snipsels that are in at least one active collection
    has_backlinks = (
        db.session.execute(
            db.select(db.func.count(SnipselCollectionRef.snipsel_id.distinct()))
            .join(Snipsel, Snipsel.id == SnipselCollectionRef.snipsel_id)
            .join(CollectionSnipsel, CollectionSnipsel.snipsel_id == Snipsel.id)
            .join(Collection, Collection.id == CollectionSnipsel.collection_id)
            .where(
                SnipselCollectionRef.collection_id == collection_id,
                Snipsel.deleted_at.is_(None),
                Collection.deleted_at.is_(None),
            )
        ).scalar()
        or 0
    )

    if has_backlinks > 0:
        raise api_error(
            400,
            "has_backlinks",
            "Cannot delete collection because it is referenced in snipsels.",
        )

    snipsel_count = (
        db.session.execute(
            db.select(db.func.count())
            .select_from(CollectionSnipsel)
            .join(Snipsel, Snipsel.id == CollectionSnipsel.snipsel_id)
            .where(
                CollectionSnipsel.collection_id == collection_id,
                Snipsel.deleted_at.is_(None),
            )
        ).scalar()
        or 0
    )

    from snipsel_api.routes_attachments import delete_collection_header_attachments

    delete_collection_header_attachments(collection_id)

    if snipsel_count == 0:
        db.session.execute(
            db.delete(CollectionSnipsel).where(CollectionSnipsel.collection_id == c.id)
        )
        db.session.execute(
            db.delete(CollectionShare).where(CollectionShare.collection_id == c.id)
        )
        db.session.execute(
            db.delete(CollectionFavorite).where(
                CollectionFavorite.collection_id == c.id
            )
        )
        db.session.execute(
            db.delete(CollectionVisit).where(CollectionVisit.collection_id == c.id)
        )
        db.session.execute(
            db.delete(SnipselCollectionRef).where(
                SnipselCollectionRef.collection_id == c.id
            )
        )
        db.session.execute(
            db.delete(Notification).where(Notification.collection_id == c.id)
        )
        db.session.delete(c)
    else:
        c.deleted_at = datetime.utcnow()
        c.deleted_by_id = user.id
        if c.list_for_day is not None:
            c.list_for_day = None

    db.session.commit()
    # Notify all users with access that the collection list changed (it's gone)
    sse_bus.publish(_collection_user_ids(c), {"type": "collection_list_changed"},
                   origin_client_id=request.headers.get("X-Client-Id"))
    return json_response({"ok": True})


@collections_bp.get("/recent")
@require_auth
def list_recent_collections():
    user = current_user()
    stmt = (
        db.select(Collection)
        .join(CollectionVisit, CollectionVisit.collection_id == Collection.id)
        .where(CollectionVisit.user_id == user.id, Collection.deleted_at.is_(None))
        .order_by(CollectionVisit.visited_at.desc())
        .limit(20)
    )
    items = db.session.execute(stmt).scalars().all()
    return json_response(
        {"collections": [{"id": c.id, "title": c.title, "icon": c.icon} for c in items]}
    )


@collections_bp.delete("/recent")
@require_auth
def clear_recent_collections():
    user = current_user()
    db.session.execute(
        db.delete(CollectionVisit).where(CollectionVisit.user_id == user.id)
    )
    db.session.commit()
    return json_response({"ok": True})


def _get_owned_collection(user_id: str, collection_id: str) -> Collection:
    c = db.session.get(Collection, collection_id)
    if not c or c.deleted_at is not None or c.owner_user_id != user_id:
        raise api_error(404, "not_found", "Collection not found")
    return c


@collections_bp.get("/autocomplete")
@require_auth
def autocomplete_collections():
    user = current_user()
    q = (request.args.get("q") or "").strip()
    if not q:
        return json_response({"collections": []})

    stmt = (
        db.select(Collection)
        .outerjoin(
            CollectionShare,
            db.and_(
                CollectionShare.collection_id == Collection.id,
                CollectionShare.shared_with_user_id == user.id,
            ),
        )
        .where(
            Collection.deleted_at.is_(None),
            Collection.archived_at.is_(None),
            db.or_(
                Collection.owner_user_id == user.id,
                CollectionShare.permission.in_(["read", "write"]),
            ),
            Collection.title.ilike(f"%{q}%"),
        )
        .order_by(Collection.title.asc())
        .limit(10)
    )
    items = db.session.execute(stmt).scalars().all()
    return json_response(
        {"collections": [{"id": c.id, "title": c.title, "icon": c.icon} for c in items]}
    )


@collections_bp.get("/<collection_id>/backlinks")
@require_auth
def list_collection_backlinks(collection_id: str):
    user = current_user()
    if not can_read_collection(user.id, collection_id):
        raise api_error(403, "forbidden", "You do not have access to this collection")

    accessible_ids = (
        db.session.execute(
            db.select(Collection.id)
            .outerjoin(
                CollectionShare,
                db.and_(
                    CollectionShare.collection_id == Collection.id,
                    CollectionShare.shared_with_user_id == user.id,
                ),
            )
            .where(
                Collection.deleted_at.is_(None),
                db.or_(
                    Collection.owner_user_id == user.id,
                    CollectionShare.permission.in_(["read", "write"]),
                ),
            )
        )
        .scalars()
        .all()
    )

    stmt = (
        db.select(
            Snipsel,
            Collection.id.label("parent_collection_id"),
            Collection.title.label("parent_collection_title"),
            Collection.icon.label("parent_collection_icon"),
            CollectionSnipsel.position.label("snipsel_position"),
        )
        .join(SnipselCollectionRef, SnipselCollectionRef.snipsel_id == Snipsel.id)
        .join(CollectionSnipsel, CollectionSnipsel.snipsel_id == Snipsel.id)
        .join(Collection, Collection.id == CollectionSnipsel.collection_id)
        .where(
            SnipselCollectionRef.collection_id == collection_id,
            Snipsel.deleted_at.is_(None),
            Collection.deleted_at.is_(None),
            Collection.id.in_(accessible_ids),
        )
        .order_by(Collection.title.asc(), CollectionSnipsel.position.asc())
    )

    rows = db.session.execute(stmt).all()
    out = []
    for s, pid, ptitle, picon, pos in rows:
        out.append(
            {
                "snipsel_id": s.id,
                "snipsel_content": (s.content_markdown or "")[:100],
                "collection_id": pid,
                "collection_title": ptitle,
                "collection_icon": picon,
                "position": pos,
            }
        )
    return json_response({"backlinks": out})


def _collection_json(c: Collection) -> dict:
    return {
        "id": c.id,
        "title": c.title,
        "icon": c.icon,
        "header_image_url": c.header_image_url,
        "header_color": c.header_color,
        "header_image_position": c.header_image_position,
        "header_image_x_position": c.header_image_x_position,
        "header_image_zoom": c.header_image_zoom,
        "is_template": bool(c.is_template),
        "default_snipsel_type": c.default_snipsel_type,
        "archived": c.archived_at is not None,
        "is_passcode_protected": bool(c.is_passcode_protected),
        "show_completed_tasks": bool(c.show_completed_tasks),
        "mute_notifications": bool(c.mute_notifications),
        "exclude_from_todo_list": bool(c.exclude_from_todo_list),
        "list_for_day": c.list_for_day.isoformat() if c.list_for_day else None,
        "created_at": c.created_at.isoformat() + "Z",
        "modified_at": c.modified_at.isoformat() + "Z",
        "modified_by_id": c.modified_by_id,
        "modified_by_username": c.modified_by.username if c.modified_by else None,
        "public_token": c.public_token,
    }


@collections_bp.get("/<collection_id>/shares")
@require_auth
def list_shares(collection_id: str):
    user = current_user()
    c = _get_owned_collection(user.id, collection_id)
    _ = c
    rows = (
        db.session.execute(
            db.select(CollectionShare)
            .where(CollectionShare.collection_id == collection_id)
            .order_by(CollectionShare.created_at.asc())
        )
        .scalars()
        .all()
    )
    user_ids = [r.shared_with_user_id for r in rows]
    users_by_id = {
        u.id: u.username
        for u in (
            db.session.execute(db.select(User).where(User.id.in_(user_ids)))
            .scalars()
            .all()
            if user_ids
            else []
        )
    }
    return json_response(
        {
            "shares": [
                {
                    "id": r.id,
                    "shared_with_user_id": r.shared_with_user_id,
                    "shared_with_username": users_by_id.get(r.shared_with_user_id),
                    "permission": r.permission,
                    "created_at": r.created_at.isoformat() + "Z",
                }
                for r in rows
            ]
        }
    )


@collections_bp.post("/<collection_id>/favorite")
@require_auth
def favorite_collection(collection_id: str):
    user = current_user()
    if not can_read_collection(user.id, collection_id):
        raise api_error(404, "not_found", "Collection not found")
    c = db.session.get(Collection, collection_id)
    if not c or c.deleted_at is not None:
        raise api_error(404, "not_found", "Collection not found")

    existing = (
        db.session.execute(
            db.select(CollectionFavorite).where(
                CollectionFavorite.user_id == user.id,
                CollectionFavorite.collection_id == c.id,
            )
        )
        .scalars()
        .first()
    )
    if not existing:
        db.session.add(CollectionFavorite(user_id=user.id, collection_id=c.id))
        db.session.commit()
    return json_response({"ok": True})


@collections_bp.delete("/<collection_id>/favorite")
@require_auth
def unfavorite_collection(collection_id: str):
    user = current_user()
    existing = (
        db.session.execute(
            db.select(CollectionFavorite).where(
                CollectionFavorite.user_id == user.id,
                CollectionFavorite.collection_id == collection_id,
            )
        )
        .scalars()
        .first()
    )
    if existing:
        db.session.delete(existing)
        db.session.commit()
    return json_response({"ok": True})


@collections_bp.post("/<collection_id>/shares")
@require_auth
@enforce_json
def create_share(collection_id: str):
    user = current_user()
    c = _get_owned_collection(user.id, collection_id)
    data = request.get_json() or {}

    shared_with_user_id = (data.get("shared_with_user_id") or "").strip()
    permission = (data.get("permission") or "").strip()
    if permission not in {"read", "write"}:
        raise api_error(400, "invalid_input", "permission must be read or write")
    if not shared_with_user_id:
        raise api_error(400, "invalid_input", "shared_with_user_id is required")
    if shared_with_user_id == c.owner_user_id:
        raise api_error(400, "invalid_input", "cannot share with owner")

    target = db.session.get(User, shared_with_user_id)
    if not target or target.deleted_at is not None or not target.is_active:
        raise api_error(400, "invalid_input", "user not found")

    existing = (
        db.session.execute(
            db.select(CollectionShare).where(
                CollectionShare.collection_id == collection_id,
                CollectionShare.shared_with_user_id == shared_with_user_id,
            )
        )
        .scalars()
        .first()
    )
    if existing:
        existing.permission = permission
        db.session.commit()
        return json_response({"share": {"id": existing.id}})

    if shared_with_user_id == "public":
        if not c.public_token:
            c.public_token = str(uuid.uuid4())
            db.session.add(c)

    s = CollectionShare(
        collection_id=collection_id,
        shared_with_user_id=shared_with_user_id,
        permission=permission,
        created_by_user_id=user.id,
    )
    db.session.add(s)

    if shared_with_user_id != "public":
        n = Notification(
            user_id=shared_with_user_id,
            message=f"{user.username} shared collection '{c.title}' with you.",
            collection_id=collection_id,
        )
        db.session.add(n)

    db.session.commit()
    return json_response({"share": {"id": s.id}}, status=201)


@collections_bp.delete("/<collection_id>/shares/<share_id>")
@require_auth
def delete_share(collection_id: str, share_id: str):
    user = current_user()
    _get_owned_collection(user.id, collection_id)
    s = db.session.get(CollectionShare, share_id)
    if not s or s.collection_id != collection_id:
        raise api_error(404, "not_found", "Share not found")
    if s.shared_with_user_id == "public":
        c = db.session.get(Collection, collection_id)
        if c:
            c.public_token = None
            db.session.add(c)

    db.session.delete(s)
    db.session.commit()
    return json_response({"ok": True})


@collections_bp.get("/trash")
@require_auth
def list_trash_collections():
    user = current_user()
    stmt = (
        db.select(Collection)
        .where(Collection.owner_user_id == user.id, Collection.deleted_at.is_not(None))
        .order_by(Collection.deleted_at.desc())
    )
    items = db.session.execute(stmt).scalars().all()

    out = []
    for c in items:
        j = _collection_json(c)
        j["deleted_at"] = c.deleted_at.isoformat() + "Z" if c.deleted_at else None
        out.append(j)

    return json_response({"collections": out})


@collections_bp.delete("/trash")
@require_auth
def empty_trash_collections():
    user = current_user()
    stmt = db.select(Collection).where(
        Collection.owner_user_id == user.id, Collection.deleted_at.is_not(None)
    )
    cols = db.session.execute(stmt).scalars().all()

    from snipsel_api.models import (
        CollectionSnipsel,
        CollectionShare,
        CollectionFavorite,
        CollectionVisit,
        SnipselCollectionRef,
        Notification,
    )
    from snipsel_api.routes_attachments import delete_collection_header_attachments

    deleted_count = 0
    for c in cols:
        delete_collection_header_attachments(c.id)

        # Manually clear relationships without cascade
        db.session.execute(
            db.delete(CollectionSnipsel).where(CollectionSnipsel.collection_id == c.id)
        )
        db.session.execute(
            db.delete(CollectionShare).where(CollectionShare.collection_id == c.id)
        )
        db.session.execute(
            db.delete(CollectionFavorite).where(
                CollectionFavorite.collection_id == c.id
            )
        )
        db.session.execute(
            db.delete(CollectionVisit).where(CollectionVisit.collection_id == c.id)
        )
        db.session.execute(
            db.delete(SnipselCollectionRef).where(
                SnipselCollectionRef.collection_id == c.id
            )
        )
        db.session.execute(
            db.delete(Notification).where(Notification.collection_id == c.id)
        )

        db.session.delete(c)
        deleted_count += 1

    db.session.commit()
    return json_response({"ok": True, "deleted": deleted_count})


@collections_bp.post("/<collection_id>/restore")
@require_auth
def restore_collection(collection_id: str):
    user = current_user()
    c = db.session.get(Collection, collection_id)
    if not c or c.owner_user_id != user.id:
        raise api_error(404, "not_found", "Collection not found")

    if c.deleted_at is None:
        return json_response({"collection": _collection_json(c)})

    c.deleted_at = None
    c.deleted_by_id = None
    c.modified_at = datetime.utcnow()
    c.modified_by_id = user.id

    db.session.commit()
    return json_response({"collection": _collection_json(c)})


@collections_bp.delete("/trash/<collection_id>")
@require_auth
def permanent_delete_collection(collection_id: str):
    user = current_user()
    c = db.session.get(Collection, collection_id)
    if not c or c.owner_user_id != user.id:
        raise api_error(404, "not_found", "Collection not found")

    if c.deleted_at is None:
        raise api_error(400, "invalid_state", "Collection is not in the trash")

    from snipsel_api.models import (
        CollectionSnipsel,
        CollectionShare,
        CollectionFavorite,
        CollectionVisit,
        SnipselCollectionRef,
        Notification,
    )
    from snipsel_api.routes_attachments import delete_collection_header_attachments

    delete_collection_header_attachments(c.id)

    # Manually clear relationships without cascade
    db.session.execute(
        db.delete(CollectionSnipsel).where(CollectionSnipsel.collection_id == c.id)
    )
    db.session.execute(
        db.delete(CollectionShare).where(CollectionShare.collection_id == c.id)
    )
    db.session.execute(
        db.delete(CollectionFavorite).where(CollectionFavorite.collection_id == c.id)
    )
    db.session.execute(
        db.delete(CollectionVisit).where(CollectionVisit.collection_id == c.id)
    )
    db.session.execute(
        db.delete(SnipselCollectionRef).where(
            SnipselCollectionRef.collection_id == c.id
        )
    )
    db.session.execute(
        db.delete(Notification).where(Notification.collection_id == c.id)
    )

    db.session.delete(c)
    db.session.commit()

    return json_response({"ok": True, "deleted": 1})
