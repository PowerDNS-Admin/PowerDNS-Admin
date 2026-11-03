"""Record host and user agent on activity and API history

Revision ID: d8e9f0a1b4c6
Revises: c7d8e9f0a1b3
Create Date: 2026-11-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'd8e9f0a1b4c6'
down_revision = 'c7d8e9f0a1b3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'history',
        sa.Column('host', sa.String(length=255), nullable=True))
    op.add_column(
        'history',
        sa.Column('user_agent', sa.String(length=512), nullable=True))
    op.add_column(
        'api_history',
        sa.Column('host', sa.String(length=255), nullable=True))
    op.add_column(
        'api_history',
        sa.Column('user_agent', sa.String(length=512), nullable=True))


def downgrade():
    op.drop_column('api_history', 'user_agent')
    op.drop_column('api_history', 'host')
    op.drop_column('history', 'user_agent')
    op.drop_column('history', 'host')
