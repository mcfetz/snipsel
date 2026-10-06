import logging

from flask import Blueprint, jsonify, request

from snipsel_api import models
from snipsel_api.auth_session import current_user, require_auth
from snipsel_api.extensions import db

logger = logging.getLogger(__name__)

bp = Blueprint("reactions", __name__)


@bp.route("/snipsels/<snipsel_id>/reactions", methods=["POST"])
@require_auth
def toggle_reaction(snipsel_id):
    user = current_user()
    data = request.get_json() or {}
    emoji = data.get("emoji")

    if not emoji:
        logger.warning(
            f"Reaction toggle failed: emoji is required. Snipsel: {snipsel_id}"
        )
        return jsonify({"error": "Emoji is required"}), 400

    snipsel = db.session.get(models.Snipsel, snipsel_id)
    if not snipsel:
        logger.warning(f"Reaction toggle failed: snipsel {snipsel_id} not found")
        return jsonify({"error": "Snipsel not found"}), 404

    if snipsel.created_by_id == user.id:
        logger.warning(
            f"User {user.username} tried to react to their own snipsel {snipsel_id}"
        )
        return jsonify({"error": "You cannot react to your own snipsel"}), 403

    # Check if the user has access to the snipsel (at least read access to any collection it's in)
    # For now, we assume if they have the ID, they can react (similar to other snipsel interactions
    # if not explicitly scoped by collection).
    # However, a more robust check would involve checking collection access.

    existing = db.session.execute(
        db.select(models.SnipselReaction).where(
            models.SnipselReaction.snipsel_id == snipsel_id,
            models.SnipselReaction.user_id == user.id,
            models.SnipselReaction.emoji == emoji,
        )
    ).scalar_one_or_none()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        logger.info(
            f"User {user.username} removed reaction {emoji} from snipsel {snipsel_id}"
        )
        return jsonify({"message": "Reaction removed", "active": False})
    else:
        reaction = models.SnipselReaction(
            snipsel_id=snipsel_id, user_id=user.id, emoji=emoji
        )
        db.session.add(reaction)

        # Create notification for creator if it's someone else reacting
        if snipsel.created_by_id != user.id:
            from snipsel_api.routes_snipsels import _is_snipsel_muted

            if not _is_snipsel_muted(snipsel_id):
                msg = f'{user.username} reacted with {emoji} to your snipsel: "{snipsel.content_markdown[:50] if snipsel.content_markdown else "..."}"'
                n = models.Notification(
                    user_id=snipsel.created_by_id, message=msg, snipsel_id=snipsel_id
                )
                db.session.add(n)

        db.session.commit()
        logger.info(
            f"User {user.username} added reaction {emoji} to snipsel {snipsel_id}"
        )
        return jsonify({"message": "Reaction added", "active": True})
