"""Add unique index to settings table keys

Revision ID: b24bf17725d2
Revises: 0967658d9c0d
Create Date: 2021-12-12 20:29:17.103441

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b24bf17725d2'
down_revision = '0967658d9c0d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(op.f('ix_setting_name'), 'setting', ['name'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_setting_name'), table_name='setting')
