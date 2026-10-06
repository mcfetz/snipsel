import sqlalchemy as sa
from alembic import op

revision = '55b4a88dc9c3'
down_revision = '0f3f3c9c1c1a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('collections', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_template', sa.Boolean(), server_default=sa.text('0'), nullable=False))

    with op.batch_alter_table('collections', schema=None) as batch_op:
        batch_op.alter_column('is_template', server_default=None)

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('day_collection_template_id', sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            'fk_users_day_collection_template_id',
            'collections',
            ['day_collection_template_id'],
            ['id'],
        )


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_day_collection_template_id', type_='foreignkey')
        batch_op.drop_column('day_collection_template_id')

    with op.batch_alter_table('collections', schema=None) as batch_op:
        batch_op.drop_column('is_template')
