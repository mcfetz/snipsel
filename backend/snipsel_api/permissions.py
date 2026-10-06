from __future__ import annotations

from datetime import datetime, timedelta

from flask import session

from snipsel_api.extensions import db
from snipsel_api.models import Collection, CollectionShare, CollectionSnipsel, utcnow


def get_collection_access_level(user_id: str, collection_id: str) -> str | None:
    c = db.session.get(Collection, collection_id)
    if not c or c.deleted_at is not None:
        return None
    if c.owner_user_id == user_id:
        return "owner"

    perm = (
        db.session.execute(
            db.select(CollectionShare.permission)
            .where(
                CollectionShare.collection_id == collection_id,
                CollectionShare.shared_with_user_id == user_id,
            )
            .limit(1)
        )
        .scalars()
        .first()
    )
    if perm == "write":
        return "write"
    if perm == "read":
        return "read"
    return None


def can_read_collection(user_id: str, collection_id: str) -> bool:
    return get_collection_access_level(user_id, collection_id) in {
        "owner",
        "write",
        "read",
    }


def can_write_collection(user_id: str, collection_id: str) -> bool:
    return get_collection_access_level(user_id, collection_id) in {"owner", "write"}


def can_read_snipsel_via_collections(user_id: str, snipsel_id: str) -> bool:
    count = (
        db.session.execute(
            db.select(db.func.count())
            .select_from(CollectionSnipsel)
            .join(Collection, Collection.id == CollectionSnipsel.collection_id)
            .outerjoin(
                CollectionShare,
                db.and_(
                    CollectionShare.collection_id == Collection.id,
                    CollectionShare.shared_with_user_id == user_id,
                ),
            )
            .where(
                CollectionSnipsel.snipsel_id == snipsel_id,
                Collection.deleted_at.is_(None),
                db.or_(
                    Collection.owner_user_id == user_id,
                    CollectionShare.permission.in_(["read", "write"]),
                ),
            )
        ).scalar()
        or 0
    )
    return count > 0


def can_write_snipsel_via_collections(user_id: str, snipsel_id: str) -> bool:
    count = (
        db.session.execute(
            db.select(db.func.count())
            .select_from(CollectionSnipsel)
            .join(Collection, Collection.id == CollectionSnipsel.collection_id)
            .outerjoin(
                CollectionShare,
                db.and_(
                    CollectionShare.collection_id == Collection.id,
                    CollectionShare.shared_with_user_id == user_id,
                ),
            )
            .where(
                CollectionSnipsel.snipsel_id == snipsel_id,
                Collection.deleted_at.is_(None),
                db.or_(
                    Collection.owner_user_id == user_id,
                    CollectionShare.permission == "write",
                ),
            )
        ).scalar()
        or 0
    )
    return count > 0


PASSCODE_GRACE_MINUTES = 2


def is_passcode_unlocked(collection_id: str) -> bool:
    """Returns True if the current session has a valid passcode unlock for this collection."""
    verified_at_str = session.get("passcode_verified_at")
    verified_cid = session.get("passcode_verified_collection_id")

    # Sticky unlock: always allow if this is the active collection
    if verified_cid == collection_id:
        return True

    # Grace period: allow if verified within the last 2 minutes
    if verified_at_str:
        try:
            verified_at = datetime.fromisoformat(verified_at_str)
            if utcnow() - verified_at < timedelta(minutes=PASSCODE_GRACE_MINUTES):
                return True
        except ValueError:
            pass

    return False
