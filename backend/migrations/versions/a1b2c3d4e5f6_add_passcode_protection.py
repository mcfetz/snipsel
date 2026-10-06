"""add passcode protection

Revision ID: a1b2c3d4e5f6
Revises: 0ff7dff48ccd
Create Date: 2026-02-26 17:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "0ff7dff48ccd"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("passcode_hash", sa.String(length=255), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "passcode_failed_attempts",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )

    with op.batch_alter_table("collections", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_passcode_protected",
                sa.Boolean(),
                nullable=False,
                server_default="0",
            )
        )


def downgrade():
    with op.batch_alter_table("collections", schema=None) as batch_op:
        batch_op.drop_column("is_passcode_protected")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("passcode_failed_attempts")
        batch_op.drop_column("passcode_hash")
