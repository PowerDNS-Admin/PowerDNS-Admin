"""Add shared authentication throttle counters

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-11-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'auth_attempt',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scope', sa.String(length=16), nullable=False),
        sa.Column('subject', sa.String(length=160), nullable=False),
        sa.Column('failures', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('lockouts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('window_started', sa.DateTime(), nullable=True),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('seen_values', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'scope', 'subject', name='uix_auth_attempt_scope_subject'),
    )
    op.create_index(
        'ix_auth_attempt_updated_at', 'auth_attempt', ['updated_at'])


def downgrade():
    op.drop_index('ix_auth_attempt_updated_at', table_name='auth_attempt')
    op.drop_table('auth_attempt')
