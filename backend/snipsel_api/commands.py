from __future__ import annotations
import click
import os
from flask.cli import with_appcontext
from snipsel_api.extensions import db
from snipsel_api import models
from snipsel_api.routes_attachments import (
    _resolve_attachment_path,
    _resolve_thumbnail_path,
)


@click.command("db-init")
@with_appcontext
def db_init():
    """Initialize the database."""
    db.create_all()
    print("Database initialized.")


@click.command("cleanup")
@with_appcontext
def cleanup():
    """Completely delete all snipsels and collections marked as deleted, including attachments."""
    deleted_snipsels = (
        db.session.execute(
            db.select(models.Snipsel).where(models.Snipsel.deleted_at.isnot(None))
        )
        .scalars()
        .all()
    )

    snipsel_count = len(deleted_snipsels)
    attachment_count = 0

    for snipsel in deleted_snipsels:
        for att in snipsel.attachments:
            file_path = _resolve_attachment_path(att.storage_path)
            thumb_path = (
                _resolve_thumbnail_path(att.thumbnail_path)
                if att.thumbnail_path
                else None
            )

            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    attachment_count += 1
                except OSError:
                    pass

            if thumb_path and os.path.exists(thumb_path):
                try:
                    os.remove(thumb_path)
                    attachment_count += 1
                except OSError:
                    pass

            db.session.delete(att)

        # Delete related entities explicitly to avoid foreign key constraint errors
        db.session.execute(
            db.delete(models.CollectionSnipsel).where(
                models.CollectionSnipsel.snipsel_id == snipsel.id
            )
        )
        db.session.execute(
            db.delete(models.SnipselTag).where(
                models.SnipselTag.snipsel_id == snipsel.id
            )
        )
        db.session.execute(
            db.delete(models.SnipselMention).where(
                models.SnipselMention.snipsel_id == snipsel.id
            )
        )
        db.session.execute(
            db.delete(models.SnipselLink).where(
                (models.SnipselLink.from_snipsel_id == snipsel.id)
                | (models.SnipselLink.to_snipsel_id == snipsel.id)
            )
        )
        db.session.execute(
            db.delete(models.SnipselCollectionRef).where(
                models.SnipselCollectionRef.snipsel_id == snipsel.id
            )
        )
        db.session.execute(
            db.delete(models.Notification).where(
                models.Notification.snipsel_id == snipsel.id
            )
        )

        db.session.delete(snipsel)

    deleted_collections = (
        db.session.execute(
            db.select(models.Collection).where(models.Collection.deleted_at.isnot(None))
        )
        .scalars()
        .all()
    )

    collection_count = len(deleted_collections)

    for collection in deleted_collections:
        db.session.execute(
            db.delete(models.CollectionSnipsel).where(
                models.CollectionSnipsel.collection_id == collection.id
            )
        )
        db.session.execute(
            db.delete(models.CollectionShare).where(
                models.CollectionShare.collection_id == collection.id
            )
        )
        db.session.execute(
            db.delete(models.CollectionFavorite).where(
                models.CollectionFavorite.collection_id == collection.id
            )
        )
        db.session.execute(
            db.delete(models.SnipselCollectionRef).where(
                models.SnipselCollectionRef.collection_id == collection.id
            )
        )
        db.session.execute(
            db.delete(models.Notification).where(
                models.Notification.collection_id == collection.id
            )
        )
        db.session.execute(
            db.delete(models.CollectionVisit).where(
                models.CollectionVisit.collection_id == collection.id
            )
        )

        # nullify day_collection_template_id in users
        db.session.execute(
            db.update(models.User)
            .where(models.User.day_collection_template_id == collection.id)
            .values(day_collection_template_id=None)
        )

        db.session.delete(collection)

    db.session.commit()
    print(
        f"Cleanup complete: {snipsel_count} snipsels, {collection_count} collections, and {attachment_count} attachment files deleted."
    )


@click.command("process-reminders")
@with_appcontext
def process_reminders_command():
    """Check for due reminders and create notifications."""
    from snipsel_api.reminders import process_reminders as run_process
    from snipsel_api.reminders import process_habit_reminders

    count = run_process()
    habit_count = process_habit_reminders()
    print(f"Processed {count} snipsel reminders and {habit_count} habit reminders.")
