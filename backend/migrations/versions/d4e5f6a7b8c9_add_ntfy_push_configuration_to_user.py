"""add ntfy push configuration to user

Revision ID: d4e5f6a7b8c9
Revises: b4c5d6e7f8a9
Create Date: 2026-10-17 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d4e5f6a7b8c9"
down_revision = "b4c5d6e7f8a9"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("ntfy_url", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("ntfy_topic", sa.String(length=255), nullable=True)
        )
        batch_op.add_column(
            sa.Column("ntfy_token", sa.String(length=255), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "ntfy_enabled",
                sa.Boolean(),
                server_default=sa.text("0"),
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "ntfy_replace_web_push",
                sa.Boolean(),
                server_default=sa.text("0"),
                nullable=False,
            )
        )

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column("ntfy_enabled", server_default=None)
        batch_op.alter_column("ntfy_replace_web_push", server_default=None)


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("ntfy_replace_web_push")
        batch_op.drop_column("ntfy_enabled")
        batch_op.drop_column("ntfy_token")
        batch_op.drop_column("ntfy_topic")
        batch_op.drop_column("ntfy_url")
