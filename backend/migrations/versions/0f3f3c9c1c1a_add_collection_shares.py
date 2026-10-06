import sqlalchemy as sa
from alembic import op

revision = "0f3f3c9c1c1a"
down_revision = "8735f6f3794b"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "collection_shares",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("collection_id", sa.String(length=36), nullable=False),
        sa.Column("shared_with_user_id", sa.String(length=36), nullable=False),
        sa.Column("permission", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=False),
        sa.CheckConstraint(
            "permission in ('read','write')", name="ck_collection_shares_permission"
        ),
        sa.ForeignKeyConstraint(["collection_id"], ["collections.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["shared_with_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "collection_id",
            "shared_with_user_id",
            name="uq_collection_share_collection_user",
        ),
    )
    with op.batch_alter_table("collection_shares", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_collection_shares_collection_id"),
            ["collection_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_collection_shares_shared_with_user_id"),
            ["shared_with_user_id"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("collection_shares", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_collection_shares_shared_with_user_id"))
        batch_op.drop_index(batch_op.f("ix_collection_shares_collection_id"))
    op.drop_table("collection_shares")
