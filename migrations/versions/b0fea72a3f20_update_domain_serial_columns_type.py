"""Update domain serial columns type

Revision ID: b0fea72a3f20
Revises: 856bb94b7040
Create Date: 2019-12-20 09:18:51.541569

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b0fea72a3f20'
down_revision = '856bb94b7040'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('domain') as batch_op:
        batch_op.alter_column('serial',
                              existing_type=sa.Integer(),
                              type_=sa.BigInteger())
        batch_op.alter_column('notified_serial',
                              existing_type=sa.Integer(),
                              type_=sa.BigInteger())


def downgrade():
    with op.batch_alter_table('domain') as batch_op:
        batch_op.alter_column('serial',
                              existing_type=sa.BigInteger(),
                              type_=sa.Integer())
        batch_op.alter_column('notified_serial',
                              existing_type=sa.BigInteger(),
                              type_=sa.Integer())
