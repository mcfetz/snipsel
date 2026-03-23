from __future__ import annotations

import hashlib
import os
import secrets
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

from flask import Blueprint, current_app, request
from PIL import Image

from snipsel_api.auth_session import (
    current_user,
    json_response,
    require_auth,
)
from snipsel_api.errors import api_error
from snipsel_api.extensions import db
from snipsel_api.models import (
    User,
    UserApiKey,
    Collection,
    CollectionSnipsel,
    Snipsel,
    Tag,
    SnipselTag,
    Attachment,
)

api_keys_bp = Blueprint("api_keys", __name__)


def _hash_key(key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


def _generate_api_key() -> str:
    """Generate a new random API key."""
    return f"snipsel_{secrets.token_urlsafe(32)}"


@api_keys_bp.get("/api_keys")
@require_auth
def list_api_keys():
    """List all API keys for the current user (without the actual key values)."""
    user = current_user()
    rows = (
        db.session.execute(
            db.select(UserApiKey)
            .where(UserApiKey.user_id == user.id)
            .order_by(UserApiKey.created_at.desc())
        )
        .scalars()
        .all()
    )
    return json_response(
        {
            "api_keys": [
                {
                    "id": k.id,
                    "name": k.name,
                    "created_at": k.created_at.isoformat() if k.created_at else None,
                    "last_used_at": k.last_used_at.isoformat()
                    if k.last_used_at
                    else None,
                }
                for k in rows
            ]
        }
    )


@api_keys_bp.post("/api_keys")
@require_auth
def create_api_key():
    """Create a new API key for the current user."""
    user = current_user()
    data = request.get_json() or {}
    name = data.get("name", "API Key").strip() or "API Key"

    # Generate a new API key
    raw_key = _generate_api_key()
    key_hash = _hash_key(raw_key)

    api_key = UserApiKey(
        user_id=user.id,
        name=name,
        key_hash=key_hash,
    )
    db.session.add(api_key)
    db.session.commit()

    # Return the raw key - this is the ONLY time it will be shown
    return json_response(
        {
            "api_key": {
                "id": api_key.id,
                "name": api_key.name,
                "key": raw_key,  # Only shown once at creation
                "created_at": api_key.created_at.isoformat()
                if api_key.created_at
                else None,
            }
        },
        status=201,
    )


@api_keys_bp.delete("/api_keys/<key_id>")
@require_auth
def delete_api_key(key_id: str):
    """Delete an API key."""
    user = current_user()

    api_key = (
        db.session.execute(
            db.select(UserApiKey).where(
                UserApiKey.id == key_id, UserApiKey.user_id == user.id
            )
        )
        .scalars()
        .first()
    )

    if not api_key:
        raise api_error(404, "not_found", "API key not found")

    db.session.delete(api_key)
    db.session.commit()

    return json_response({"ok": True})


def _get_user_from_api_key(api_key: str) -> User | None:
    """Get user from an API key."""
    key_hash = _hash_key(api_key)

    # Debug logging
    import logging

    logger = logging.getLogger(__name__)
    logger.debug(f"Looking for API key hash: {key_hash[:20]}...")
    logger.debug(
        f"Received key prefix: {api_key[:30] if len(api_key) > 30 else api_key}..."
    )

    api_key_record = (
        db.session.execute(db.select(UserApiKey).where(UserApiKey.key_hash == key_hash))
        .scalars()
        .first()
    )

    if not api_key_record:
        # Log all available keys for debugging (only in development!)
        all_keys = db.session.execute(db.select(UserApiKey)).scalars().all()
        logger.debug(f"No matching key found. Available keys in DB: {len(all_keys)}")
        for k in all_keys:
            logger.debug(f"  - Key hash prefix: {k.key_hash[:20]}...")

    if not api_key_record:
        return None

    # Update last used timestamp
    api_key_record.last_used_at = datetime.utcnow()
    db.session.commit()

    # Get the user
    user = db.session.get(User, api_key_record.user_id)
    if not user or user.deleted_at is not None or not user.is_active:
        return None

    return user


def _get_or_create_day_collection(user_id: str) -> Collection:
    """Get or create today's collection for a user."""
    from datetime import date

    today = date.today()

    # Look for today's collection
    collection = (
        db.session.execute(
            db.select(Collection).where(
                Collection.owner_user_id == user_id,
                Collection.list_for_day == today,
                Collection.deleted_at.is_(None),
            )
        )
        .scalars()
        .first()
    )

    if collection:
        return collection

    # Create a new collection for today
    collection = Collection(
        owner_user_id=user_id,
        title=today.strftime("%A, %B %d"),  # e.g., "Monday, March 23"
        icon="📅",
        list_for_day=today,
        created_by_id=user_id,
        modified_by_id=user_id,
    )
    db.session.add(collection)
    db.session.flush()

    return collection


@api_keys_bp.post("/quick_add")
def quick_add_snipsel():
    """Quickly add a snipsel using an API key.

    This endpoint is designed for external integrations like iOS Shortcuts
    or browser extensions that need to add content without full OAuth flow.
    Supports both JSON and multipart/form-data (for file uploads).
    """
    # Get API key from header (try different variants)
    api_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
    if not api_key:
        raise api_error(401, "unauthorized", "API key required")

    # Authenticate with API key
    user = _get_user_from_api_key(api_key)
    if not user:
        raise api_error(401, "unauthorized", "Invalid API key")

    # Handle both JSON and multipart/form-data
    uploaded_files = []

    if request.content_type and "multipart/form-data" in request.content_type:
        content = request.form.get("content", "").strip()
        title = request.form.get("title", "").strip()
        item_type = request.form.get("type", "note").strip().lower()
        tags_str = request.form.get("tags", "")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

        uploaded_files = request.files.getlist("file")
        uploaded_files = [f for f in uploaded_files if f and f.filename]
    else:
        data = request.get_json() or {}
        content = data.get("content", "").strip()
        title = data.get("title", "").strip()
        item_type = data.get("type", "note").strip().lower()
        tags = data.get("tags", [])

    has_files = len(uploaded_files) > 0

    if not content and not has_files:
        raise api_error(400, "invalid_input", "Content or file required")

    if item_type not in ("note", "task"):
        raise api_error(400, "invalid_input", "type must be 'note' or 'task'")

    collection = _get_or_create_day_collection(user.id)

    snipsel_type = "task" if item_type == "task" else "text"
    if has_files:
        snipsel_type = "attachment"
    elif title and not content:
        content = title

    snipsel = Snipsel(
        owner_user_id=user.id,
        type=snipsel_type,
        content_markdown=content if content else None,
        card_view=True,
        created_by_id=user.id,
        modified_by_id=user.id,
    )
    db.session.add(snipsel)
    db.session.flush()

    attachments_info = []
    if has_files:
        upload_dir = Path(current_app.config.get("SNIPSEL_UPLOAD_DIR", "./uploads"))
        upload_dir.mkdir(parents=True, exist_ok=True)

        for uploaded_file in uploaded_files:
            att_id = str(uuid.uuid4())
            safe_name = os.path.basename(uploaded_file.filename)
            storage_path = upload_dir / f"{att_id}_{safe_name}"

            uploaded_file.save(storage_path)
            size = storage_path.stat().st_size
            mime_type = uploaded_file.mimetype

            thumbnail_path: Path | None = None
            if mime_type:
                if mime_type.startswith("image/"):
                    thumbnail_path = upload_dir / f"{att_id}_thumb.jpg"
                    _write_thumbnail(storage_path, thumbnail_path)
                    snipsel.type = "image"
                elif mime_type.startswith("video/"):
                    thumbnail_path = upload_dir / f"{att_id}_video_thumb.jpg"
                    if _write_video_thumbnail(storage_path, thumbnail_path):
                        pass
                    else:
                        thumbnail_path = None

            att = Attachment(
                id=att_id,
                snipsel_id=snipsel.id,
                filename=safe_name,
                mime_type=mime_type,
                size_bytes=size,
                storage_path=str(storage_path),
                thumbnail_path=str(thumbnail_path) if thumbnail_path else None,
                created_by_id=user.id,
            )
            db.session.add(att)

            attachments_info.append(
                {
                    "id": att.id,
                    "filename": att.filename,
                    "mime_type": att.mime_type,
                    "size_bytes": att.size_bytes,
                    "has_thumbnail": att.thumbnail_path is not None,
                }
            )

    # Add to today's collection
    max_pos = (
        db.session.execute(
            db.select(db.func.max(CollectionSnipsel.position)).where(
                CollectionSnipsel.collection_id == collection.id
            )
        ).scalar()
        or 0
    )

    cs = CollectionSnipsel(
        collection_id=collection.id,
        snipsel_id=snipsel.id,
        position=max_pos + 1,
        indent=0,
    )
    db.session.add(cs)

    # Handle tags if provided
    if tags and isinstance(tags, list):
        for tag_name in tags:
            tag_name = str(tag_name).strip().lower()
            if not tag_name:
                continue

            # Get or create tag
            tag = (
                db.session.execute(
                    db.select(Tag).where(
                        Tag.name == tag_name, Tag.owner_user_id == user.id
                    )
                )
                .scalars()
                .first()
            )

            if not tag:
                tag = Tag(
                    name=tag_name,
                    owner_user_id=user.id,
                )
                db.session.add(tag)
                db.session.flush()

            # Link tag to snipsel
            snipsel_tag = SnipselTag(
                snipsel_id=snipsel.id,
                tag_id=tag.id,
            )
            db.session.add(snipsel_tag)

    db.session.commit()

    result = {
        "snipsel": {
            "id": snipsel.id,
            "type": snipsel.type,
            "content": snipsel.content_markdown,
            "created_at": snipsel.created_at.isoformat()
            if snipsel.created_at
            else None,
        },
        "collection": {
            "id": collection.id,
            "title": collection.title,
        },
    }

    if attachments_info:
        result["attachments"] = attachments_info
        result["attachment_count"] = len(attachments_info)

    return json_response(result, status=201)


def _write_thumbnail(src: Path, dst: Path) -> None:
    if Image is None:
        return
    with Image.open(src) as im:
        try:
            exif = im.getexif()
            if exif:
                orientation = exif.get(0x0112)
                if orientation == 3:
                    im = im.rotate(180, expand=True)
                elif orientation == 6:
                    im = im.rotate(270, expand=True)
                elif orientation == 8:
                    im = im.rotate(90, expand=True)
        except Exception:
            pass
        im.thumbnail((512, 512))
        im = im.convert("RGB")
        im.save(dst, format="JPEG", quality=80)


def _write_video_thumbnail(src: Path, dst: Path) -> bool:
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-ss",
            "00:00:01",
            "-vframes",
            "1",
            "-f",
            "image2",
            "-vcodec",
            "mjpeg",
            str(dst),
        ]
        result = subprocess.run(cmd, capture_output=True, check=False)
        if result.returncode == 0:
            if dst.exists():
                _write_thumbnail(dst, dst)
            return True
        else:
            cmd[cmd.index("-ss") + 1] = "00:00:00"
            result = subprocess.run(cmd, capture_output=True, check=False)
            if result.returncode == 0:
                if dst.exists():
                    _write_thumbnail(dst, dst)
                return True
    except Exception as e:
        print(f"Error generating video thumbnail: {e}")
    return False
