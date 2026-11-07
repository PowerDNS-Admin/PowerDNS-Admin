"""Add an audit table for application setting changes

Revision ID: c7d8e9f0a1b3
Revises: b6c7d8e9f0a2
Create Date: 2026-11-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c7d8e9f0a1b3'
down_revision = 'b6c7d8e9f0a2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'system_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_on', sa.DateTime(), nullable=False),
        sa.Column('setting_name', sa.String(length=64), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('username', sa.String(length=128), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('remote_addr', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_system_history_created_on', 'system_history', ['created_on'],
        unique=False)
    op.create_index(
        'ix_system_history_setting_name', 'system_history', ['setting_name'],
        unique=False)
    op.create_index(
        'ix_system_history_user_id', 'system_history', ['user_id'],
        unique=False)


def downgrade():
    op.drop_index('ix_system_history_user_id', table_name='system_history')
    op.drop_index(
        'ix_system_history_setting_name', table_name='system_history')
    op.drop_index(
        'ix_system_history_created_on', table_name='system_history')
    op.drop_table('system_history')
