"""Record the API response body on API history

Revision ID: e9f0a1b2c5d7
Revises: d8e9f0a1b4c6
Create Date: 2026-11-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'e9f0a1b2c5d7'
down_revision = 'd8e9f0a1b4c6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'api_history',
        sa.Column('response_body', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('api_history', 'response_body')
