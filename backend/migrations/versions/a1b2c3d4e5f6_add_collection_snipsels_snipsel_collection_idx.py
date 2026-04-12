"""Add composite index (snipsel_id, collection_id) on collection_snipsels for faster tag/mention lookups

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-04-12 18:58:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    # This composite index makes EXISTS(SELECT 1 FROM collection_snipsels
    # WHERE snipsel_id = ? AND collection_id IN (...)) nearly O(1) per snipsel,
    # which is critical for the tags/mentions aggregation queries.
    with op.batch_alter_table('collection_snipsels', schema=None) as batch_op:
        batch_op.create_index(
            'ix_collection_snipsels_snipsel_collection',
            ['snipsel_id', 'collection_id'],
        )


def downgrade():
    with op.batch_alter_table('collection_snipsels', schema=None) as batch_op:
        batch_op.drop_index('ix_collection_snipsels_snipsel_collection')
