"""update domain type length

Revision ID: f41520e41cee
Revises: 6ea7dc05f496
Create Date: 2023-01-10 11:56:28.538485

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f41520e41cee'
down_revision = '6ea7dc05f496'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('domain') as batch_op:
        batch_op.alter_column('type',
                              existing_type=sa.String(length=6),
                              type_=sa.String(length=8))


def downgrade():
    with op.batch_alter_table('domain') as batch_op:
        batch_op.alter_column('type',
                              existing_type=sa.String(length=8),
                              type_=sa.String(length=6))
        
