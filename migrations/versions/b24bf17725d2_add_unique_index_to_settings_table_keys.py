"""Add unique index to settings table keys

Revision ID: b24bf17725d2
Revises: f41520e41cee
Create Date: 2023-02-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b24bf17725d2'
down_revision = 'f41520e41cee'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(op.f('ix_setting_name'), 'setting', ['name'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_setting_name'), table_name='setting')
