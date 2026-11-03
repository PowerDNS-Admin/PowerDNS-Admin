"""Add an audit table for /api requests

Revision ID: b6c7d8e9f0a2
Revises: a5b6c7d8e9f1
Create Date: 2026-11-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b6c7d8e9f0a2'
down_revision = 'a5b6c7d8e9f1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'api_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_on', sa.DateTime(), nullable=False),
        sa.Column('method', sa.String(length=16), nullable=False),
        sa.Column('path', sa.String(length=512), nullable=False),
        sa.Column('query_string', sa.Text(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('remote_addr', sa.String(length=255), nullable=True),
        sa.Column('auth_type', sa.String(length=16), nullable=False),
        sa.Column('authenticated', sa.Boolean(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('username', sa.String(length=128), nullable=True),
        sa.Column('apikey_id', sa.Integer(), nullable=True),
        sa.Column('apikey_description', sa.String(length=255), nullable=True),
        sa.Column('request_body', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_api_history_created_on', 'api_history', ['created_on'],
        unique=False)
    op.create_index(
        'ix_api_history_user_id', 'api_history', ['user_id'],
        unique=False)
    op.create_index(
        'ix_api_history_apikey_id', 'api_history', ['apikey_id'],
        unique=False)


def downgrade():
    op.drop_index('ix_api_history_apikey_id', table_name='api_history')
    op.drop_index('ix_api_history_user_id', table_name='api_history')
    op.drop_index('ix_api_history_created_on', table_name='api_history')
    op.drop_table('api_history')
