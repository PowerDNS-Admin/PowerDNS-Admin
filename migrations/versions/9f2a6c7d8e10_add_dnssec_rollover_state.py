"""Add DNSSEC rollover state

Revision ID: 9f2a6c7d8e10
Revises: b24bf17725d2
Create Date: 2026-07-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '9f2a6c7d8e10'
down_revision = 'b24bf17725d2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'dnssec_rollover',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('domain_id', sa.Integer(), nullable=False),
        sa.Column('rollover_type', sa.String(length=16), nullable=False),
        sa.Column('keytype', sa.String(length=8), nullable=False),
        sa.Column('state', sa.String(length=32), nullable=False),
        sa.Column('old_key_ids', sa.Text(), nullable=False),
        sa.Column('new_key_ids', sa.Text(), nullable=False),
        sa.Column('algorithm', sa.String(length=32), nullable=False),
        sa.Column('bits', sa.Integer(), nullable=False),
        sa.Column('started_by', sa.String(length=128), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('not_before', sa.DateTime(), nullable=True),
        sa.Column('parent_ds_confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ['domain_id'], ['domain.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_dnssec_rollover_active'), 'dnssec_rollover',
        ['active'], unique=False)
    op.create_index(
        op.f('ix_dnssec_rollover_domain_id'), 'dnssec_rollover',
        ['domain_id'], unique=False)
    op.create_index(
        op.f('ix_dnssec_rollover_state'), 'dnssec_rollover',
        ['state'], unique=False)


def downgrade():
    op.drop_index(
        op.f('ix_dnssec_rollover_state'), table_name='dnssec_rollover')
    op.drop_index(
        op.f('ix_dnssec_rollover_domain_id'), table_name='dnssec_rollover')
    op.drop_index(
        op.f('ix_dnssec_rollover_active'), table_name='dnssec_rollover')
    op.drop_table('dnssec_rollover')
