"""Add indexes for API access paths

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-08-03 00:00:00.000000

"""
from alembic import op


revision = 'f4a5b6c7d8e9'
down_revision = 'e3f4a5b6c7d8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        'ix_account_user_user_id_account_id',
        'account_user', ['user_id', 'account_id'], unique=False)
    op.create_index(
        'ix_apikey_account_apikey_id_account_id',
        'apikey_account', ['apikey_id', 'account_id'], unique=False)
    op.create_index(
        'ix_domain_apikey_apikey_id_domain_id',
        'domain_apikey', ['apikey_id', 'domain_id'], unique=False)
    op.create_index(
        'ix_domain_setting_domain_id_setting',
        'domain_setting', ['domain_id', 'setting'], unique=False)
    op.create_index(
        'ix_domain_user_user_id_domain_id',
        'domain_user', ['user_id', 'domain_id'], unique=False)


def downgrade():
    op.drop_index(
        'ix_domain_user_user_id_domain_id', table_name='domain_user')
    op.drop_index(
        'ix_domain_setting_domain_id_setting', table_name='domain_setting')
    op.drop_index(
        'ix_domain_apikey_apikey_id_domain_id', table_name='domain_apikey')
    op.drop_index(
        'ix_apikey_account_apikey_id_account_id',
        table_name='apikey_account')
    op.drop_index(
        'ix_account_user_user_id_account_id', table_name='account_user')
