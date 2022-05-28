"""Remove all setting in the DB

Revision ID: 31a4ed468b18
Revises: 4a666113c7bb
Create Date: 2018-08-21 17:12:30.058782

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '31a4ed468b18'
down_revision = '4a666113c7bb'
branch_labels = None
depends_on = None


def upgrade():
    # delete all settings from "setting" table.
    # PDA should work without initial settings in the DB
    # Once user change the settings from UI, they will be
    # written to the DB.
    op.execute("DELETE FROM setting")

    with op.batch_alter_table('setting') as batch_op:
        # drop view column since we don't need it
        batch_op.drop_column('view')

def downgrade():
    with op.batch_alter_table('setting') as batch_op:
        batch_op.add_column(sa.Column('view', sa.String(length=64), nullable=True))
