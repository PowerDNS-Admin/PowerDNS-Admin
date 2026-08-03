"""Add TOTP replay protection

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-08-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'd2e3f4a5b6c7'
down_revision = 'c1d2e3f4a5b6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'user',
        sa.Column('otp_last_used', sa.BigInteger(), nullable=True),
    )


def downgrade():
    op.drop_column('user', 'otp_last_used')
