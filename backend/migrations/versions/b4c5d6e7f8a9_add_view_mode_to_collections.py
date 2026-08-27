"""add view_mode to collections

Revision ID: b4c5d6e7f8a9
Revises: 781ded07f37f
Create Date: 2026-08-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b4c5d6e7f8a9'
down_revision = '781ded07f37f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('collections', schema=None) as batch_op:
        batch_op.add_column(sa.Column('view_mode', sa.String(length=32), nullable=True, server_default='list'))


def downgrade():
    with op.batch_alter_table('collections', schema=None) as batch_op:
        batch_op.drop_column('view_mode')
