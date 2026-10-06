import sqlalchemy as sa
from alembic import op

revision = "9f2a5b1a2c77"
down_revision = "55b4a88dc9c3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "collection_favorites",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("collection_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["collection_id"], ["collections.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id", "collection_id"),
    )
    with op.batch_alter_table("collection_favorites", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_collection_favorites_user_id"), ["user_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_collection_favorites_collection_id"),
            ["collection_id"],
            unique=False,
        )

    op.execute(
        "INSERT INTO collection_favorites (user_id, collection_id, created_at) "
        "SELECT owner_user_id, id, modified_at FROM collections WHERE is_favorite = 1"
    )

    with op.batch_alter_table("collections", schema=None) as batch_op:
        batch_op.drop_column("is_favorite")


def downgrade():
    with op.batch_alter_table("collections", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_favorite", sa.Boolean(), server_default=sa.text("0"), nullable=False
            )
        )
    with op.batch_alter_table("collections", schema=None) as batch_op:
        batch_op.alter_column("is_favorite", server_default=None)

    op.execute(
        "UPDATE collections SET is_favorite = 1 WHERE id IN (SELECT collection_id FROM collection_favorites)"
    )

    with op.batch_alter_table("collection_favorites", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_collection_favorites_collection_id"))
        batch_op.drop_index(batch_op.f("ix_collection_favorites_user_id"))
    op.drop_table("collection_favorites")
