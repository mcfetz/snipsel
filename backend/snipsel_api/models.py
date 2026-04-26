from __future__ import annotations
from typing import Optional

import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from snipsel_api.extensions import db


def utcnow() -> datetime:
    return datetime.utcnow()


SnipselType = Enum(
    "text",
    "task",
    "link_external",
    "link_internal",
    "attachment",
    "image",
    name="snipsel_type",
)


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    anonymized_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    default_collection_header_color: Mapped[Optional[str]] = mapped_column(
        String(7), nullable=True
    )

    day_collection_template_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("collections.id"),
        nullable=True,
    )

    carry_over_open_tasks: Mapped[bool] = mapped_column(default=True, nullable=False)
    theme: Mapped[str] = mapped_column(String(20), nullable=False, default="system")

    passcode_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    passcode_failed_attempts: Mapped[int] = mapped_column(default=0, nullable=False)

    otp_secret: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    otp_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)

    ai_llm_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_model_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ai_api_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    light_background_color: Mapped[Optional[str]] = mapped_column(
        String(7), nullable=True
    )
    dark_background_color: Mapped[Optional[str]] = mapped_column(
        String(7), nullable=True
    )
    is_admin: Mapped[bool] = mapped_column(default=False, nullable=False)
    diced_moments_tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Collection(db.Model):
    __tablename__ = "collections"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    owner_user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    icon: Mapped[str] = mapped_column(String(8), nullable=False, default="🗒")
    header_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    header_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    header_image_position: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, default="50%"
    )
    header_image_x_position: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, default="50%"
    )
    header_image_zoom: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=1.0
    )

    is_template: Mapped[bool] = mapped_column(default=False, nullable=False)

    is_passcode_protected: Mapped[bool] = mapped_column(default=False, nullable=False)
    show_completed_tasks: Mapped[bool] = mapped_column(default=True, nullable=False)
    mute_notifications: Mapped[bool] = mapped_column(default=False, nullable=False)
    exclude_from_todo_list: Mapped[bool] = mapped_column(default=False, nullable=False)

    default_snipsel_type: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )

    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    list_for_day: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
    created_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    modified_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )
    modified_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    twos_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=True
    )
    public_token: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )

    owner = relationship("User", foreign_keys=[owner_user_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    modified_by = relationship("User", foreign_keys=[modified_by_id])

    __table_args__ = (
        UniqueConstraint(
            "owner_user_id", "list_for_day", name="uq_collection_owner_day"
        ),
        Index("ix_collections_owner_archived", "owner_user_id", "archived_at"),
    )


class CollectionShare(db.Model):
    __tablename__ = "collection_shares"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    collection_id: Mapped[str] = mapped_column(
        ForeignKey("collections.id"), nullable=False, index=True
    )
    shared_with_user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    permission: Mapped[str] = mapped_column(String(16), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
    created_by_user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    collection = relationship("Collection")
    shared_with = relationship("User", foreign_keys=[shared_with_user_id])
    created_by = relationship("User", foreign_keys=[created_by_user_id])

    __table_args__ = (
        UniqueConstraint(
            "collection_id",
            "shared_with_user_id",
            name="uq_collection_share_collection_user",
        ),
        CheckConstraint(
            "permission in ('read','write')", name="ck_collection_shares_permission"
        ),
    )


class CollectionFavorite(db.Model):
    __tablename__ = "collection_favorites"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    collection_id: Mapped[str] = mapped_column(
        ForeignKey("collections.id"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    user = relationship("User")
    collection = relationship("Collection")


class Snipsel(db.Model):
    __tablename__ = "snipsels"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    owner_user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    type: Mapped[str] = mapped_column(SnipselType, nullable=False, index=True)
    card_view: Mapped[bool] = mapped_column(default=True, nullable=False)

    content_markdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    geo_lat: Mapped[Optional[float]] = mapped_column(nullable=True, index=True)
    geo_lng: Mapped[Optional[float]] = mapped_column(nullable=True, index=True)
    geo_accuracy_m: Mapped[Optional[float]] = mapped_column(nullable=True)

    task_done: Mapped[int] = mapped_column(default=0, nullable=False)
    done_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    done_by_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    external_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    external_label: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    internal_target_snipsel_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("snipsels.id"), nullable=True
    )
    reminder_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reminder_rrule: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
    created_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    modified_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )
    modified_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    deleted_by_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    diced_count: Mapped[int] = mapped_column(default=0, nullable=False, index=True)

    owner = relationship("User", foreign_keys=[owner_user_id])
    done_by = relationship("User", foreign_keys=[done_by_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    modified_by = relationship("User", foreign_keys=[modified_by_id])

    attachments: Mapped[list["Attachment"]] = relationship(
        "Attachment", back_populates="snipsel", cascade="all, delete-orphan"
    )
    tags: Mapped[list["SnipselTag"]] = relationship(
        "SnipselTag", back_populates="snipsel", cascade="all, delete-orphan"
    )
    mentions: Mapped[list["SnipselMention"]] = relationship(
        "SnipselMention", back_populates="snipsel", cascade="all, delete-orphan"
    )
    reactions: Mapped[list["SnipselReaction"]] = relationship(
        "SnipselReaction", back_populates="snipsel", cascade="all, delete-orphan"
    )

    def get_reaction_summary(self, user_id: str):
        summary = {}
        for r in self.reactions:
            e = r.emoji
            if e not in summary:
                summary[e] = {"emoji": e, "count": 0, "me": False}
            summary[e]["count"] += 1
            if r.user_id == user_id:
                summary[e]["me"] = True
        return sorted(summary.values(), key=lambda x: x["count"], reverse=True)

    __table_args__ = (
        CheckConstraint(
            "(task_done = 0) OR (task_done = 1) OR (task_done = 2)",
            name="ck_snipsels_task_done_bool",
        ),
    )


class CollectionSnipsel(db.Model):
    __tablename__ = "collection_snipsels"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    collection_id: Mapped[str] = mapped_column(
        ForeignKey("collections.id"), nullable=False, index=True
    )
    snipsel_id: Mapped[str] = mapped_column(
        ForeignKey("snipsels.id"), nullable=False, index=True
    )

    position: Mapped[int] = mapped_column(nullable=False, default=0)
    indent: Mapped[int] = mapped_column(nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    collection = relationship("Collection")
    snipsel = relationship("Snipsel")

    __table_args__ = (
        UniqueConstraint("collection_id", "snipsel_id", name="uq_collection_snipsel"),
        Index(
            "ix_collection_snipsels_collection_position", "collection_id", "position"
        ),
        CheckConstraint("indent >= 0", name="ck_collection_snipsels_indent_nonneg"),
    )


class Tag(db.Model):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    owner_user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("owner_user_id", "name", name="uq_tags_owner_name"),
    )


class SnipselTag(db.Model):
    __tablename__ = "snipsel_tags"

    snipsel_id: Mapped[str] = mapped_column(ForeignKey("snipsels.id"), primary_key=True)
    tag_id: Mapped[str] = mapped_column(ForeignKey("tags.id"), primary_key=True, index=True)

    snipsel = relationship("Snipsel", back_populates="tags")
    tag = relationship("Tag")


class Mention(db.Model):
    __tablename__ = "mentions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    owner_user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("owner_user_id", "name", name="uq_mentions_owner_name"),
    )


class SnipselMention(db.Model):
    __tablename__ = "snipsel_mentions"

    snipsel_id: Mapped[str] = mapped_column(ForeignKey("snipsels.id"), primary_key=True)
    mention_id: Mapped[str] = mapped_column(ForeignKey("mentions.id"), primary_key=True, index=True)

    snipsel = relationship("Snipsel", back_populates="mentions")
    mention = relationship("Mention")


class SnipselReaction(db.Model):
    __tablename__ = "snipsel_reactions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    snipsel_id: Mapped[str] = mapped_column(
        ForeignKey("snipsels.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    emoji: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    snipsel = relationship("Snipsel", back_populates="reactions")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint(
            "snipsel_id", "user_id", "emoji", name="uq_snipsel_reaction_user_emoji"
        ),
    )


class SnipselLink(db.Model):
    __tablename__ = "snipsel_links"

    from_snipsel_id: Mapped[str] = mapped_column(
        ForeignKey("snipsels.id"), primary_key=True
    )
    to_snipsel_id: Mapped[str] = mapped_column(
        ForeignKey("snipsels.id"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    from_snipsel = relationship("Snipsel", foreign_keys=[from_snipsel_id])
    to_snipsel = relationship("Snipsel", foreign_keys=[to_snipsel_id])

    __table_args__ = (Index("ix_snipsel_links_to", "to_snipsel_id"),)


class SnipselCollectionRef(db.Model):
    __tablename__ = "snipsel_collection_refs"

    snipsel_id: Mapped[str] = mapped_column(ForeignKey("snipsels.id"), primary_key=True)
    collection_id: Mapped[str] = mapped_column(
        ForeignKey("collections.id"), primary_key=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    snipsel = relationship("Snipsel")
    collection = relationship("Collection")


class Attachment(db.Model):
    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    snipsel_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("snipsels.id"), nullable=True, index=True
    )
    collection_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("collections.id"), nullable=True, index=True
    )

    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    size_bytes: Mapped[int] = mapped_column(nullable=False)

    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
    created_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    snipsel: Mapped[Optional[Snipsel]] = relationship(
        "Snipsel", back_populates="attachments"
    )
    collection: Mapped[Optional[Collection]] = relationship("Collection")


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    user = relationship("User")


class Notification(db.Model):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(default=False, nullable=False)

    snipsel_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("snipsels.id"), nullable=True
    )
    collection_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("collections.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    user = relationship("User")
    snipsel = relationship("Snipsel")
    collection = relationship("Collection")


class CollectionVisit(db.Model):
    __tablename__ = "collection_visits"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    collection_id: Mapped[str] = mapped_column(
        ForeignKey("collections.id"), primary_key=True
    )
    visited_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    user = relationship("User")
    collection = relationship("Collection")


class PushSubscription(db.Model):
    __tablename__ = "push_subscriptions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    endpoint: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    keys_p256dh: Mapped[str] = mapped_column(String(255), nullable=False)
    keys_auth: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    user = relationship("User")


class UserPasskey(db.Model):
    __tablename__ = "user_passkeys"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    credential_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    sign_count: Mapped[int] = mapped_column(default=0, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    user = relationship("User")


class UserApiKey(db.Model):
    __tablename__ = "user_api_keys"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False, default="API Key")
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user = relationship("User")


class UserOidcLink(db.Model):
    __tablename__ = "user_oidc_links"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="oidc")
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("provider", "subject", name="uq_oidc_provider_subject"),
    )


class AiPromptHistory(db.Model):
    __tablename__ = "ai_prompt_history"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    starred: Mapped[bool] = mapped_column(default=False, nullable=False)
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "prompt", name="uq_ai_prompt_history_user_prompt"),
    )
