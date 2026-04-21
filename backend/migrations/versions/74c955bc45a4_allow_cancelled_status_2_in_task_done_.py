"""Allow cancelled status 2 in task_done check constraint

Revision ID: 74c955bc45a4
Revises: 1fc39a90bbc0
Create Date: 2026-04-21 09:01:45.267644

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '74c955bc45a4'
down_revision = '1fc39a90bbc0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('snipsels', schema=None) as batch_op:
        batch_op.drop_constraint('ck_snipsels_task_done_bool', type_='check')
        batch_op.create_check_constraint(
            'ck_snipsels_task_done_bool',
            '(task_done = 0) OR (task_done = 1) OR (task_done = 2)'
        )


def downgrade():
    with op.batch_alter_table('snipsels', schema=None) as batch_op:
        batch_op.drop_constraint('ck_snipsels_task_done_bool', type_='check')
        batch_op.create_check_constraint(
            'ck_snipsels_task_done_bool',
            '(task_done = 0) OR (task_done = 1)'
        )
