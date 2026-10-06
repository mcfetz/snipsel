from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path

from flask import Blueprint, current_app, request, send_file, session
from PIL import Image

from snipsel_api.auth_session import current_user, json_response, require_auth
from snipsel_api.errors import api_error
from snipsel_api.extensions import db
from snipsel_api.models import (
    Attachment,
    Collection,
    CollectionSnipsel,
    Mention,
    Snipsel,
    SnipselMention,
    User,
    utcnow,
)
from snipsel_api.permissions import (
    can_read_collection,
    can_read_snipsel_via_collections,
    can_write_collection,
    can_write_snipsel_via_collections,
)
from snipsel_api.routes_snipsels import _touch_collections_for_snipsel

logger = logging.getLogger(__name__)

attachments_bp = Blueprint("attachments", __name__)


@attachments_bp.post("/snipsels/<snipsel_id>/attachments")
@require_auth
def upload_attachment(snipsel_id: str):
    user = current_user()
    snipsel = db.session.get(Snipsel, snipsel_id)
    if (
        not snipsel
        or snipsel.deleted_at is not None
        or (
            snipsel.owner_user_id != user.id
            and not can_write_snipsel_via_collections(user.id, snipsel_id)
        )
    ):
        raise api_error(404, "not_found", "Snipsel not found")

    if "file" not in request.files:
        raise api_error(400, "invalid_input", "file is required")

    file = request.files["file"]
    if not file or not file.filename:
        raise api_error(400, "invalid_input", "file is required")

    upload_dir = Path(current_app.config.get("SNIPSEL_UPLOAD_DIR", "./uploads"))
    upload_dir.mkdir(parents=True, exist_ok=True)

    att_id = str(uuid.uuid4())
    safe_name = os.path.basename(file.filename)
    storage_path = upload_dir / f"{att_id}_{safe_name}"

    file.save(storage_path)
    size = storage_path.stat().st_size
    mime_type = file.mimetype

    thumbnail_path: Path | None = None
    if mime_type:
        if mime_type.startswith("image/"):
            thumbnail_path = upload_dir / f"{att_id}_thumb.jpg"
            _write_thumbnail(storage_path, thumbnail_path)
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
    _touch_collections_for_snipsel(snipsel_id=snipsel_id, modified_by_id=user.id)
    db.session.commit()

    return json_response(
        {
            "attachment": {
                "id": att.id,
                "filename": att.filename,
                "mime_type": att.mime_type,
                "size_bytes": att.size_bytes,
                "has_thumbnail": att.thumbnail_path is not None,
            }
        },
        status=201,
    )


@attachments_bp.post("/collections/<collection_id>/header-image")
@require_auth
def upload_collection_header(collection_id: str):
    user = current_user()
    collection = db.session.get(Collection, collection_id)
    if (
        not collection
        or collection.deleted_at is not None
        or (
            collection.owner_user_id != user.id
            and not can_write_collection(user.id, collection_id)
        )
    ):
        raise api_error(404, "not_found", "Collection not found")

    if "file" not in request.files:
        raise api_error(400, "invalid_input", "file is required")

    file = request.files["file"]
    if not file or not file.filename:
        raise api_error(400, "invalid_input", "file is required")

    upload_dir = Path(current_app.config.get("SNIPSEL_UPLOAD_DIR", "./uploads"))
    upload_dir.mkdir(parents=True, exist_ok=True)

    att_id = str(uuid.uuid4())
    safe_name = os.path.basename(file.filename)
    storage_path = upload_dir / f"{att_id}_{safe_name}"

    file.save(storage_path)
    size = storage_path.stat().st_size
    mime_type = file.mimetype

    thumbnail_path: Path | None = None
    if mime_type and mime_type.startswith("image/"):
        thumbnail_path = upload_dir / f"{att_id}_header_thumb.jpg"
        _write_thumbnail(storage_path, thumbnail_path, header=True)

    # Clean up old header attachments if they exist
    delete_collection_header_attachments(collection.id)

    att = Attachment(
        id=att_id,
        collection_id=collection.id,
        filename=safe_name,
        mime_type=mime_type,
        size_bytes=size,
        storage_path=str(storage_path),
        thumbnail_path=str(thumbnail_path) if thumbnail_path else None,
        created_by_id=user.id,
    )
    db.session.add(att)

    collection.header_image_url = f"/api/attachments/{att_id}"
    collection.modified_at = utcnow()
    collection.modified_by_id = user.id

    db.session.commit()

    return json_response(
        {
            "collection": {
                "id": collection.id,
                "header_image_url": collection.header_image_url,
                "header_image_position": collection.header_image_position,
                "header_attachment_id": att_id,
            }
        },
        status=201,
    )


@attachments_bp.get("/attachments/<attachment_id>")
def download_attachment(attachment_id: str):
    user_id = session.get("user_id")
    public_authorized = session.get("public_authorized_collections") or []

    att = db.session.get(Attachment, attachment_id)
    if not att:
        raise api_error(404, "not_found", "Attachment not found")

    is_authorized = False

    if user_id:
        # Standard user check
        if att.snipsel_id:
            snipsel = db.session.get(Snipsel, att.snipsel_id)
            if snipsel and snipsel.deleted_at is None:
                if snipsel.owner_user_id == user_id or can_read_snipsel_via_collections(
                    user_id, snipsel.id
                ):
                    is_authorized = True
                else:
                    user = db.session.get(User, user_id)
                    uname = (getattr(user, "username", "") or "").strip().casefold()
                    if uname:
                        is_mentioned = (
                            db.session.execute(
                                db.select(db.func.count())
                                .select_from(SnipselMention)
                                .join(Mention, Mention.id == SnipselMention.mention_id)
                                .where(
                                    SnipselMention.snipsel_id == snipsel.id,
                                    Mention.name == uname,
                                )
                            ).scalar()
                            or 0
                        ) > 0
                        if is_mentioned:
                            is_authorized = True
        elif att.collection_id:
            if can_read_collection(user_id, att.collection_id):
                is_authorized = True

    if not is_authorized and public_authorized:
        # Check public access
        if att.collection_id:
            if att.collection_id in public_authorized:
                is_authorized = True
        elif att.snipsel_id:
            # Check if snipsel is in any of the authorized public collections
            in_public = (
                db.session.execute(
                    db.select(db.func.count())
                    .select_from(CollectionSnipsel)
                    .where(
                        CollectionSnipsel.snipsel_id == att.snipsel_id,
                        CollectionSnipsel.collection_id.in_(public_authorized),
                    )
                ).scalar()
                or 0
            ) > 0
            if in_public:
                is_authorized = True

    if not is_authorized:
        raise api_error(401 if not user_id else 403, "unauthorized", "Access denied")

    path = _resolve_attachment_path(att)
    if not path:
        raise api_error(404, "not_found", "Attachment file missing")

    try:
        return send_file(str(path), as_attachment=True, download_name=att.filename)
    except FileNotFoundError:
        raise api_error(404, "not_found", "Attachment file missing")


@attachments_bp.get("/attachments/<attachment_id>/thumbnail")
def download_thumbnail(attachment_id: str):
    user_id = session.get("user_id")
    public_authorized = session.get("public_authorized_collections") or []

    att = db.session.get(Attachment, attachment_id)
    if not att or not att.thumbnail_path:
        raise api_error(404, "not_found", "Thumbnail not found")

    is_authorized = False

    if user_id:
        # Standard user check
        if att.snipsel_id:
            snipsel = db.session.get(Snipsel, att.snipsel_id)
            if snipsel and snipsel.deleted_at is None:
                if snipsel.owner_user_id == user_id or can_read_snipsel_via_collections(
                    user_id, snipsel.id
                ):
                    is_authorized = True
                else:
                    user = db.session.get(User, user_id)
                    uname = (getattr(user, "username", "") or "").strip().casefold()
                    if uname:
                        is_mentioned = (
                            db.session.execute(
                                db.select(db.func.count())
                                .select_from(SnipselMention)
                                .join(Mention, Mention.id == SnipselMention.mention_id)
                                .where(
                                    SnipselMention.snipsel_id == snipsel.id,
                                    Mention.name == uname,
                                )
                            ).scalar()
                            or 0
                        ) > 0
                        if is_mentioned:
                            is_authorized = True
        elif att.collection_id:
            if can_read_collection(user_id, att.collection_id):
                is_authorized = True

    if not is_authorized and public_authorized:
        # Check public access
        if att.collection_id:
            if att.collection_id in public_authorized:
                is_authorized = True
        elif att.snipsel_id:
            # Check if snipsel is in any of the authorized public collections
            in_public = (
                db.session.execute(
                    db.select(db.func.count())
                    .select_from(CollectionSnipsel)
                    .where(
                        CollectionSnipsel.snipsel_id == att.snipsel_id,
                        CollectionSnipsel.collection_id.in_(public_authorized),
                    )
                ).scalar()
                or 0
            ) > 0
            if in_public:
                is_authorized = True

    if not is_authorized:
        raise api_error(401 if not user_id else 403, "unauthorized", "Access denied")

    # Try to resolve or regenerate thumbnail
    path = _resolve_thumbnail_path(att)
    if not path:
        raise api_error(404, "not_found", "Thumbnail file missing")

    try:
        return send_file(str(path), as_attachment=False)
    except FileNotFoundError:
        raise api_error(404, "not_found", "Thumbnail file missing")


@attachments_bp.delete("/attachments/<attachment_id>")
@require_auth
def delete_attachment(attachment_id: str):
    user = current_user()
    att = db.session.get(Attachment, attachment_id)
    if not att:
        raise api_error(404, "not_found", "Attachment not found")

    if att.snipsel_id:
        snipsel = db.session.get(Snipsel, att.snipsel_id)
        if (
            not snipsel
            or snipsel.deleted_at is not None
            or (
                snipsel.owner_user_id != user.id
                and not can_write_snipsel_via_collections(user.id, snipsel.id)
            )
        ):
            raise api_error(404, "not_found", "Attachment not found")
    elif att.collection_id:
        if not can_write_collection(user.id, att.collection_id):
            raise api_error(404, "not_found", "Attachment not found")
    else:
        raise api_error(404, "not_found", "Attachment not found")

    file_path = _resolve_attachment_path(att)
    thumb_path = _resolve_thumbnail_path(att, regenerate=False)

    for p in [thumb_path, file_path]:
        if not p:
            continue
        try:
            p.unlink(missing_ok=True)
        except OSError:
            pass

    db.session.delete(att)
    if att.snipsel_id:
        _touch_collections_for_snipsel(
            snipsel_id=att.snipsel_id, modified_by_id=user.id
        )
    elif att.collection_id:
        coll = db.session.get(Collection, att.collection_id)
        if coll:
            coll.modified_at = utcnow()
            coll.modified_by_id = user.id
    db.session.commit()
    return json_response({"ok": True})


def delete_collection_header_attachments(collection_id: str):
    """Deletes all attachments associated with a collection's header."""
    header_atts = (
        db.session.execute(
            db.select(Attachment).where(Attachment.collection_id == collection_id)
        )
        .scalars()
        .all()
    )
    for att in header_atts:
        # Resolve paths without triggering regeneration
        paths_to_delete = []
        if att.storage_path:
            paths_to_delete.append(Path(att.storage_path))
        if att.thumbnail_path:
            paths_to_delete.append(Path(att.thumbnail_path))

        for p in paths_to_delete:
            if p and p.exists():
                try:
                    p.unlink(missing_ok=True)
                except OSError:
                    pass
        db.session.delete(att)
    db.session.flush()


def delete_attachment_file(att: Attachment) -> None:
    """Deletes the physical files associated with an attachment, given the Attachment object."""
    file_path = _resolve_attachment_path(att)
    thumb_path = _resolve_thumbnail_path(att, regenerate=False)

    for p in [thumb_path, file_path]:
        if not p:
            continue
        try:
            p.unlink(missing_ok=True)
        except OSError:
            pass


def _resolve_attachment_path(att: Attachment) -> Path | None:
    upload_dir = Path(current_app.config.get("SNIPSEL_UPLOAD_DIR", "./uploads"))
    expected = f"{att.id}_{att.filename}"

    backend_dir = Path(current_app.root_path).resolve().parent

    candidates: list[Path] = []
    if att.storage_path:
        p = Path(att.storage_path)
        if p.is_absolute():
            candidates.append(p)
        else:
            candidates.extend(
                [
                    Path(current_app.instance_path) / p,
                    Path(current_app.root_path) / p,
                    backend_dir / p,
                    Path.cwd() / p,
                ]
            )

    candidates.extend(
        [
            upload_dir / expected,
            Path(current_app.instance_path) / "uploads" / expected,
            Path(current_app.root_path) / "uploads" / expected,
            backend_dir / "uploads" / expected,
            Path(__file__).resolve().parent / "uploads" / expected,
            Path.cwd() / "uploads" / expected,
        ]
    )

    found = _first_existing(candidates)
    if found and att.storage_path != str(found):
        att.storage_path = str(found)
        db.session.commit()
    return found


def _resolve_thumbnail_path(att: Attachment, regenerate: bool = True) -> Path | None:
    upload_dir = Path(current_app.config.get("SNIPSEL_UPLOAD_DIR", "./uploads"))
    expected = f"{att.id}_thumb.jpg"

    backend_dir = Path(current_app.root_path).resolve().parent

    candidates: list[Path] = []
    if att.thumbnail_path:
        p = Path(att.thumbnail_path)
        if p.is_absolute():
            candidates.append(p)
        else:
            candidates.extend(
                [
                    Path(current_app.instance_path) / p,
                    Path(current_app.root_path) / p,
                    backend_dir / p,
                    Path.cwd() / p,
                ]
            )

    candidates.extend(
        [
            upload_dir / expected,
            Path(current_app.instance_path) / "uploads" / expected,
            Path(current_app.root_path) / "uploads" / expected,
            backend_dir / "uploads" / expected,
            Path(__file__).resolve().parent / "uploads" / expected,
            Path.cwd() / "uploads" / expected,
        ]
    )

    found = _first_existing(candidates)

    # If thumbnail file is missing but original exists, regenerate it
    if not found and regenerate:
        # Find original image
        original_candidates = []
        if att.storage_path:
            sp = Path(att.storage_path)
            if sp.is_absolute():
                original_candidates.append(sp)
            else:
                original_candidates.extend(
                    [
                        Path(current_app.instance_path) / att.storage_path,
                        Path(current_app.root_path) / att.storage_path,
                        backend_dir / att.storage_path,
                        Path.cwd() / att.storage_path,
                        upload_dir / att.storage_path,
                        upload_dir / f"{att.id}_{att.filename}",
                    ]
                )

        original = _first_existing(original_candidates)
        if original and original.exists():
            thumb_name = f"{att.id}_thumb.jpg"
            if "_header_thumb.jpg" in (att.thumbnail_path or ""):
                thumb_name = f"{att.id}_header_thumb.jpg"
            elif "_video_thumb.jpg" in (att.thumbnail_path or "") or (
                att.mime_type and att.mime_type.startswith("video/")
            ):
                thumb_name = f"{att.id}_video_thumb.jpg"

            thumb_path = upload_dir / thumb_name

            success = False
            if "_video_thumb.jpg" in thumb_name:
                success = _write_video_thumbnail(original, thumb_path)
            else:
                _write_thumbnail(
                    original, thumb_path, header=("_header_thumb.jpg" in thumb_name)
                )
                success = True

            if success:
                att.thumbnail_path = str(thumb_path)
                db.session.commit()
                found = thumb_path

    if found and att.thumbnail_path != str(found):
        att.thumbnail_path = str(found)
        db.session.commit()
    return found


def _first_existing(paths: list[Path]) -> Path | None:
    for p in paths:
        try:
            if p.exists():
                return p
        except OSError:
            continue
    return None


def _write_thumbnail(src: Path, dst: Path, header: bool = False) -> None:
    if Image is None:
        return
    with Image.open(src) as im:
        # Handle EXIF orientation
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
            logger.debug("EXIF orientation handling failed", exc_info=True)

        if header:
            # For headers, we want a reasonably wide thumbnail to support "move" functionality
            # without pre-cropping. We resize to 1200px width and maintain aspect ratio.
            max_w = 1200
            if im.width > max_w:
                w_percent = max_w / float(im.width)
                h_size = int(float(im.height) * float(w_percent))
                im = im.resize((max_w, h_size), Image.Resampling.LANCZOS)

            # Save as optimized JPEG
            im.convert("RGB").save(str(dst), "JPEG", quality=85, optimize=True)
        else:
            im.thumbnail((512, 512))
            im = im.convert("RGB")
            im.save(dst, format="JPEG", quality=80)


def _write_video_thumbnail(src: Path, dst: Path) -> bool:
    """Generates a thumbnail for a video file using ffmpeg."""
    import subprocess

    try:
        # Extract 1 frame from 1 second into the video
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
            # Resize the generated thumbnail if needed
            if dst.exists():
                _write_thumbnail(dst, dst)
            return True
        else:
            # Try at 0 seconds if 1 second fails (e.g. very short video)
            cmd[cmd.index("-ss") + 1] = "00:00:00"
            result = subprocess.run(cmd, capture_output=True, check=False)
            if result.returncode == 0:
                if dst.exists():
                    _write_thumbnail(dst, dst)
                return True
    except Exception:
        logger.warning("Error generating video thumbnail", exc_info=True)
    return False
