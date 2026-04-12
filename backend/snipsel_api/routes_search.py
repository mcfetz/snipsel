from __future__ import annotations

from datetime import date, datetime, timedelta

from flask import Blueprint, request

from sqlalchemy import literal

from snipsel_api.auth_session import current_user, json_response, require_auth
from snipsel_api.errors import api_error
from snipsel_api.extensions import db
from snipsel_api.models import (
    Attachment,
    Collection,
    CollectionShare,
    CollectionSnipsel,
    Mention,
    Snipsel,
    SnipselReaction,
    SnipselMention,
    SnipselTag,
    Tag,
    User,
)
from sqlalchemy.orm import joinedload

search_bp = Blueprint("search", __name__)


@search_bp.get("/tags")
@require_auth
def list_tags():
    user = current_user()
    scope = (request.args.get("scope") or "my").strip().lower()
    q = (request.args.get("q") or "").strip().lower()
    if scope not in {"my", "shared", "all"}:
        raise api_error(400, "invalid_input", "scope must be my, shared or all")

    accessible_collections_sq = (
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
            db.or_(Collection.owner_user_id == user.id, CollectionShare.permission.in_(["read", "write"])),
        )
    )

    rows = (
        db.session.execute(
            db.select(Tag.name, db.func.count(db.distinct(Snipsel.id)))
            .join(SnipselTag, SnipselTag.tag_id == Tag.id)
            .join(Snipsel, Snipsel.id == SnipselTag.snipsel_id)
            .join(CollectionSnipsel, CollectionSnipsel.snipsel_id == Snipsel.id)
            .where(
                CollectionSnipsel.collection_id.in_(accessible_collections_sq),
                Tag.owner_user_id == user.id if scope == "my" else Tag.owner_user_id != user.id if scope == "shared" else db.true(),
                Snipsel.deleted_at.is_(None),
                Tag.name.ilike(f"%{q}%") if q else db.true(),
            )
            .group_by(Tag.name)
            .order_by(db.func.count(db.distinct(Snipsel.id)).desc(), Tag.name.asc())
            .limit(100)
        ).all()
    )
    return json_response(
        {
            "tags": [
                {"name": name, "count": int(count)}
                for name, count in rows
                if name and name[:1].isalpha()
            ]
        }
    )


@search_bp.get("/mentions")
@require_auth
def list_mentions():
    user = current_user()
    scope = (request.args.get("scope") or "my").strip().lower()
    q = (request.args.get("q") or "").strip().lower()
    if scope not in {"my", "shared", "all"}:
        raise api_error(400, "invalid_input", "scope must be my, shared or all")

    accessible_collections_sq = (
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
            db.or_(Collection.owner_user_id == user.id, CollectionShare.permission.in_(["read", "write"])),
        )
    )

    rows = (
        db.session.execute(
            db.select(Mention.name, db.func.count(db.distinct(Snipsel.id)))
            .join(SnipselMention, SnipselMention.mention_id == Mention.id)
            .join(Snipsel, Snipsel.id == SnipselMention.snipsel_id)
            .join(CollectionSnipsel, CollectionSnipsel.snipsel_id == Snipsel.id)
            .where(
                CollectionSnipsel.collection_id.in_(accessible_collections_sq),
                Mention.owner_user_id == user.id if scope == "my" else Mention.owner_user_id != user.id if scope == "shared" else db.true(),
                Snipsel.deleted_at.is_(None),
                Mention.name.ilike(f"%{q}%") if q else db.true(),
            )
            .group_by(Mention.name)
            .order_by(db.func.count(db.distinct(Snipsel.id)).desc(), Mention.name.asc())
            .limit(100)
        ).all()
    )
    return json_response(
        {
            "mentions": [
                {"name": name, "count": int(count)}
                for name, count in rows
                if name and name[:1].isalpha()
            ]
        }
    )


@search_bp.get("/search")
@require_auth
def search():
    user = current_user()
    q = (request.args.get("q") or "").strip()
    tag = (request.args.get("tag") or "").strip().casefold() or None
    mention = (request.args.get("mention") or "").strip().casefold() or None
    mentions_me = request.args.get("mentions_me") == "1"
    scope = (request.args.get("scope") or "my").strip().lower()
    if scope not in {"my", "shared", "all"}:
        raise api_error(400, "invalid_input", "scope must be my, shared, or all")
    snipsel_type = (request.args.get("type") or "").strip() or None
    task_done_raw = (request.args.get("task_done") or "").strip()
    task_done_filter: bool | None
    if task_done_raw == "":
        task_done_filter = None
    elif task_done_raw == "1":
        task_done_filter = True
    elif task_done_raw == "0":
        task_done_filter = False
    else:
        raise api_error(400, "invalid_input", "task_done must be 0 or 1")
    include_archived = request.args.get("include_archived") == "1"
    day = request.args.get("day")
    day_parsed = date.fromisoformat(day) if day else None

    accessible_collection_ids = (
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
                db.or_(Collection.owner_user_id == user.id, CollectionShare.permission.in_(["read", "write"])),
            )
        )
        .scalars()
        .all()
    )

    writable_collection_ids = (
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
                db.or_(Collection.owner_user_id == user.id, CollectionShare.permission == "write"),
            )
        )
        .scalars()
        .all()
    )
    writable_set = set(writable_collection_ids)

    stmt = (
        db.select(
            Snipsel,
            CollectionSnipsel.collection_id.label("collection_id"),
            CollectionSnipsel.position.label("position"),
            Collection.title.label("collection_title"),
            Collection.icon.label("collection_icon"),
        )
        .join(CollectionSnipsel, CollectionSnipsel.snipsel_id == Snipsel.id)
        .join(Collection, Collection.id == CollectionSnipsel.collection_id)
        .where(
            Snipsel.deleted_at.is_(None),
            CollectionSnipsel.collection_id.in_(accessible_collection_ids) if accessible_collection_ids else db.false(),
        )
        .options(joinedload(Snipsel.reactions))
        .distinct()
    )
    if snipsel_type:
        stmt = stmt.where(Snipsel.type == snipsel_type)
    if snipsel_type == "task":
        done_val = task_done_filter if task_done_filter is not None else False
        stmt = stmt.where(Snipsel.task_done.is_(done_val))
    if q:
        # Split search query into terms and require ALL terms to match (AND search)
        # Also replace + with space to handle URL-encoded spaces
        q = q.replace('+', ' ')
        terms = q.split()
        for term in terms:
            if not term:
                continue
            like = f"%{term}%"
            stmt = stmt.where(
                db.or_(
                    Snipsel.content_markdown.ilike(like),
                    Snipsel.external_url.ilike(like),
                    Snipsel.external_label.ilike(like),
                )
            )

    if tag:
        stmt = stmt.join(SnipselTag, SnipselTag.snipsel_id == Snipsel.id).join(Tag, Tag.id == SnipselTag.tag_id)
        if scope == "shared":
            stmt = stmt.where(Tag.owner_user_id != user.id, Tag.name == tag)
        elif scope == "all":
            stmt = stmt.where(Tag.name == tag)
        else:
            stmt = stmt.where(Tag.owner_user_id == user.id, Tag.name == tag)

    if mention:
        stmt = stmt.join(SnipselMention, SnipselMention.snipsel_id == Snipsel.id).join(
            Mention, Mention.id == SnipselMention.mention_id
        )
        if scope == "shared":
            stmt = stmt.where(Mention.owner_user_id != user.id, Mention.name == mention)
        elif scope == "all":
            stmt = stmt.where(Mention.name == mention)
        else:
            stmt = stmt.where(Mention.owner_user_id == user.id, Mention.name == mention)

    if day_parsed:
        start = datetime(day_parsed.year, day_parsed.month, day_parsed.day)
        end = start + timedelta(days=1)
        stmt = stmt.where(
            db.or_(
                db.and_(Snipsel.created_at >= start, Snipsel.created_at < end),
                db.and_(Snipsel.modified_at >= start, Snipsel.modified_at < end),
            )
        )

    if snipsel_type == "task" and not mention and not q and not tag and not day_parsed:
        # For the main Todos page (no specific search terms), we exclude template collections.
        stmt = stmt.where(Collection.is_template.is_(False))

        # For task-specific scope filtering: filter by who created the task,
        # and exclude tasks that are explicitly @assigned to any known user.
        #
        # A "known user mention" subquery: snipsels that contain a @mention whose
        # name matches any registered User's username (case-insensitive).
        has_user_mention_sq = (
            db.select(literal(1))
            .select_from(SnipselMention)
            .join(Mention, Mention.id == SnipselMention.mention_id)
            .where(
                SnipselMention.snipsel_id == Snipsel.id,
                db.func.lower(Mention.name).in_(
                    db.select(db.func.lower(User.username)).scalar_subquery()
                ),
            )
            .correlate(Snipsel)
            .exists()
        )
        if scope == "my":
            stmt = stmt.where(
                Snipsel.created_by_id == user.id,
                ~has_user_mention_sq,
            )
        elif scope == "shared":
            stmt = stmt.where(
                Snipsel.created_by_id != user.id,
                ~has_user_mention_sq,
            )

    accessible_rows = db.session.execute(stmt.order_by(Snipsel.modified_at.desc()).limit(200)).unique().all()

    hits_by_id: dict[str, tuple[Snipsel, str | None, int | None, str | None, str | None, bool, bool, bool]] = {}
    for s, collection_id, position, collection_title, collection_icon in accessible_rows:
        if s.id not in hits_by_id:
            can_write = bool(s.owner_user_id == user.id or (collection_id in writable_set))
            can_toggle_task_done = bool(s.type == "task")
            hits_by_id[s.id] = (
                s,
                collection_id,
                int(position) if position is not None else None,
                collection_title,
                collection_icon,
                True,
                can_write,
                can_toggle_task_done,
            )

    if mentions_me and snipsel_type == "task" and getattr(user, "username", None):
        uname = str(user.username).casefold()
        done_val = task_done_filter if task_done_filter is not None else False
        m_stmt = (
            db.select(
                Snipsel,
            )
            .join(SnipselMention, SnipselMention.snipsel_id == Snipsel.id)
            .join(Mention, Mention.id == SnipselMention.mention_id)
            .where(
                Snipsel.deleted_at.is_(None),
                Snipsel.type == "task",
                Snipsel.task_done.is_(done_val),
                Mention.name == uname,
            )
            .options(joinedload(Snipsel.reactions))
            .distinct()
        )

        mentioned_rows = db.session.execute(m_stmt.order_by(Snipsel.modified_at.desc()).limit(200)).unique().all()
        for (s,) in mentioned_rows:
            if s.id in hits_by_id:
                continue
            hits_by_id[s.id] = (
                s,
                None,
                None,
                None,
                None,
                False,
                True,
                bool(s.type == "task"),
            )

    rows = sorted(hits_by_id.values(), key=lambda r: r[0].modified_at, reverse=True)[:200]

    collection_hits = []
    if q:
        c_stmt = db.select(Collection).where(
            Collection.owner_user_id == user.id,
            Collection.deleted_at.is_(None),
        )
        if not include_archived:
            c_stmt = c_stmt.where(Collection.archived_at.is_(None))
        c_stmt = c_stmt.where(Collection.title.ilike(f"%{q}%"))
        collection_hits = db.session.execute(c_stmt.limit(50)).scalars().all()

    return json_response(
        {
            "snipsels": [
                {
                    "id": s.id,
                    "type": s.type,
                    "content_markdown": s.content_markdown,
                    "task_done": s.task_done,
                    "done_at": s.done_at.isoformat() + "Z" if s.done_at else None,
                    "external_url": s.external_url,
                    "external_label": s.external_label,
                    "internal_target_snipsel_id": s.internal_target_snipsel_id,
                    "created_at": s.created_at.isoformat() + "Z",
                    "modified_at": s.modified_at.isoformat() + "Z",
                    "collection_id": collection_id,
                    "collection_title": collection_title,
                    "collection_icon": collection_icon,
                    "position": position,
                    "reminder_at": s.reminder_at.isoformat() + "Z" if s.reminder_at else None,
                    "reminder_rrule": s.reminder_rrule,
                    "has_collection_access": has_collection_access,
                    "has_write_access": has_write_access,
                    "can_toggle_task_done": can_toggle_task_done,
                    "reactions": s.get_reaction_summary(user.id),
                }
                for s, collection_id, position, collection_title, collection_icon, has_collection_access, has_write_access, can_toggle_task_done in rows
            ],
            "collections": [
                {
                    "id": c.id,
                    "title": c.title,
                    "icon": c.icon,
                    "list_for_day": c.list_for_day.isoformat() if c.list_for_day else None,
                }
                for c in collection_hits
            ],
        }
    )




@search_bp.get("/search/mentions/incoming")
@require_auth
def get_incoming_day_mentions():
    """Get snipsels from other users' daily collections on a specific day that mention the current user."""
    user = current_user()
    day_str = request.args.get("day")
    if not day_str:
        raise api_error(400, "invalid_input", "day parameter is required")
    
    try:
        day_parsed = date.fromisoformat(day_str)
    except ValueError:
        raise api_error(400, "invalid_input", "day must be in YYYY-MM-DD format")
    
    if not getattr(user, "username", None):
        return json_response({"snipsels": []})
    
    uname = str(user.username).casefold()
    
    # First check: how many mentions exist for this user?
    mentions_for_user = db.session.execute(
        db.select(Mention).where(Mention.name == uname)
    ).all()
    # Second check: how many daily collections exist for this day?
    daily_collections = db.session.execute(
        db.select(Collection, User.username)
        .join(User, User.id == Collection.owner_user_id)
        .where(
            Collection.deleted_at.is_(None),
            Collection.list_for_day == day_parsed,
            Collection.owner_user_id != user.id,
        )
    ).all()
    # Find snipsels from OTHER users' daily collections on this day that mention the current user
    # Note: We don't require the collection to be shared - we just need to find any daily
    # collection from another user on the same day that mentions the current user
    stmt = (
        db.select(
            Snipsel,
            CollectionSnipsel.collection_id,
            CollectionSnipsel.position,
            Collection.owner_user_id,
            User.username.label("owner_username"),
        )
        .join(SnipselMention, SnipselMention.snipsel_id == Snipsel.id)
        .join(Mention, Mention.id == SnipselMention.mention_id)
        .join(CollectionSnipsel, CollectionSnipsel.snipsel_id == Snipsel.id)
        .join(Collection, Collection.id == CollectionSnipsel.collection_id)
        .join(User, User.id == Collection.owner_user_id)
        .where(
            Snipsel.deleted_at.is_(None),
            Collection.deleted_at.is_(None),
            Collection.list_for_day == day_parsed,
            Collection.owner_user_id != user.id,
            Mention.name == uname,
        )
        .distinct()
    )
    
    rows = db.session.execute(stmt.options(joinedload(Snipsel.reactions)).order_by(Snipsel.modified_at.desc()).limit(100)).unique().all()
    
    if rows:
        # Fetch attachments for all snipsels
        snipsel_ids = [s.id for s, _, _, _, _ in rows]
        attachments = (
            db.session.execute(
                db.select(Attachment).where(Attachment.snipsel_id.in_(snipsel_ids))
            ).scalars().all()
        )
        attachments_by_snipsel = {}
        for a in attachments:
            if a.snipsel_id not in attachments_by_snipsel:
                attachments_by_snipsel[a.snipsel_id] = []
            attachments_by_snipsel[a.snipsel_id].append({
                "id": a.id,
                "filename": a.filename,
                "mime_type": a.mime_type,
                "size_bytes": a.size_bytes,
                "has_thumbnail": a.thumbnail_path is not None,
            })
        
        return json_response(
            {
                "snipsels": [
                    {
                        "id": s.id,
                        "type": s.type,
                        "content_markdown": s.content_markdown,
                        "task_done": s.task_done,
                        "done_at": s.done_at.isoformat() + "Z" if s.done_at else None,
                        "external_url": s.external_url,
                        "external_label": s.external_label,
                        "internal_target_snipsel_id": s.internal_target_snipsel_id,
                        "created_at": s.created_at.isoformat() + "Z",
                        "modified_at": s.modified_at.isoformat() + "Z",
                        "collection_id": collection_id,
                        "created_by_username": owner_username,
                        "position": int(position) if position is not None else None,
                        "reminder_at": s.reminder_at.isoformat() + "Z" if s.reminder_at else None,
                        "reminder_rrule": s.reminder_rrule,
                        "attachments": attachments_by_snipsel.get(s.id, []),
                        "reactions": s.get_reaction_summary(user.id),
                    }
                    for s, collection_id, position, owner_user_id, owner_username in rows
                ]
            }
        )
    return json_response({"snipsels": []})
