"""Add user_oidc_links table for OIDC authentication

Revision ID: f1a2b3c4d5e6
Revises: ed22a41367db
Create Date: 2026-03-30 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f1a2b3c4d5e6"
down_revision = "ed22a41367db"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_oidc_links",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "subject", name="uq_oidc_provider_subject"),
    )
    with op.batch_alter_table("user_oidc_links", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_user_oidc_links_user_id"), ["user_id"], unique=False
        )


def downgrade():
    with op.batch_alter_table("user_oidc_links", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_user_oidc_links_user_id"))
    op.drop_table("user_oidc_links")
