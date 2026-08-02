"""Set preserved history domain references to null on delete

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-08-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'e3f4a5b6c7d8'
down_revision = 'd2e3f4a5b6c7'
branch_labels = None
depends_on = None


def upgrade():
    # SQLite commonly runs without foreign-key enforcement, so legacy
    # databases can contain references to domains that no longer exist.
    # Repair those rows before creating a constraint that MySQL/PostgreSQL
    # will enforce during or after a database migration.
    op.execute(sa.text("""
        UPDATE history
        SET domain_id = NULL
        WHERE domain_id IS NOT NULL
          AND NOT EXISTS (
              SELECT 1
              FROM domain
              WHERE domain.id = history.domain_id
          )
    """))

    with op.batch_alter_table('history', schema=None) as batch_op:
        batch_op.drop_constraint('fk_domain_id', type_='foreignkey')
        batch_op.create_foreign_key(
            'fk_domain_id',
            'domain',
            ['domain_id'],
            ['id'],
            ondelete='SET NULL',
        )


def downgrade():
    with op.batch_alter_table('history', schema=None) as batch_op:
        batch_op.drop_constraint('fk_domain_id', type_='foreignkey')
        batch_op.create_foreign_key(
            'fk_domain_id',
            'domain',
            ['domain_id'],
            ['id'],
        )
