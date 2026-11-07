"""Add an account-level lock for rejected authentication codes

Revision ID: f0a1b2c3d4e5
Revises: e9f0a1b2c5d7
Create Date: 2026-11-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'f0a1b2c3d4e5'
down_revision = 'e9f0a1b2c5d7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'user',
        sa.Column(
            'otp_failed_attempts',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )
    op.add_column(
        'user',
        sa.Column('otp_locked_until', sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_column('user', 'otp_locked_until')
    op.drop_column('user', 'otp_failed_attempts')
