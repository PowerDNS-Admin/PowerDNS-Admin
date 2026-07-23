"""Add stable DNSSEC rollover key identity

Revision ID: c1d2e3f4a5b6
Revises: 9f2a6c7d8e10
Create Date: 2026-07-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c1d2e3f4a5b6'
down_revision = '9f2a6c7d8e10'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'dnssec_rollover_key',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rollover_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=8), nullable=False),
        sa.Column('backend_key_id', sa.Integer(), nullable=True),
        sa.Column('fingerprint', sa.String(length=64), nullable=False),
        sa.Column('key_tag', sa.Integer(), nullable=False),
        sa.Column('keytype', sa.String(length=8), nullable=False),
        sa.Column('algorithm', sa.String(length=32), nullable=False),
        sa.Column('bits', sa.Integer(), nullable=True),
        sa.Column('dnskey', sa.Text(), nullable=False),
        sa.Column('ds', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['rollover_id'], ['dnssec_rollover.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'rollover_id', 'role', 'fingerprint',
            name='uq_dnssec_rollover_key_identity'),
    )
    op.create_index(
        op.f('ix_dnssec_rollover_key_backend_key_id'),
        'dnssec_rollover_key', ['backend_key_id'], unique=False)
    op.create_index(
        op.f('ix_dnssec_rollover_key_fingerprint'),
        'dnssec_rollover_key', ['fingerprint'], unique=False)
    op.create_index(
        op.f('ix_dnssec_rollover_key_rollover_id'),
        'dnssec_rollover_key', ['rollover_id'], unique=False)


def downgrade():
    op.drop_index(
        op.f('ix_dnssec_rollover_key_rollover_id'),
        table_name='dnssec_rollover_key')
    op.drop_index(
        op.f('ix_dnssec_rollover_key_fingerprint'),
        table_name='dnssec_rollover_key')
    op.drop_index(
        op.f('ix_dnssec_rollover_key_backend_key_id'),
        table_name='dnssec_rollover_key')
    op.drop_table('dnssec_rollover_key')
