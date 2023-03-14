"""Add user.confirmed column

Revision ID: 3f76448bb6de
Revises: b0fea72a3f20
Create Date: 2019-12-21 17:11:36.564632

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3f76448bb6de'
down_revision = 'b0fea72a3f20'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(
            sa.Column('confirmed', sa.Boolean(), nullable=True,
                      default=False))
    with op.batch_alter_table('user') as batch_op:
        user = sa.sql.table('user', sa.sql.column('confirmed'))
        batch_op.execute(user.update().values(confirmed=False))
        batch_op.alter_column('confirmed', nullable=False, existing_type=sa.Boolean(), existing_nullable=True, existing_server_default=False)


def downgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('confirmed')
