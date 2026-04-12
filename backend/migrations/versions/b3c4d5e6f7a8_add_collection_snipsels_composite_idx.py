"""Add composite index (snipsel_id, collection_id) on collection_snipsels for faster tag/mention lookups

Revision ID: b3c4d5e6f7a8
Revises: 1826e10f56de
Create Date: 2026-04-12 19:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b3c4d5e6f7a8'
down_revision = '1826e10f56de'
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
