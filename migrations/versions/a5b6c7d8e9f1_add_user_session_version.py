"""Add a session version so password changes revoke other logins

Revision ID: a5b6c7d8e9f1
Revises: f4a5b6c7d8e9
Create Date: 2026-11-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a5b6c7d8e9f1'
down_revision = 'f4a5b6c7d8e9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'user',
        sa.Column(
            'session_version',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )


def downgrade():
    op.drop_column('user', 'session_version')
