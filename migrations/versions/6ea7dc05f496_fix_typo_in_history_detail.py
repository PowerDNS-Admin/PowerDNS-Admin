"""Fix typo in history detail

Revision ID: 6ea7dc05f496
Revises: fbc7cf864b24
Create Date: 2022-05-10 10:16:58.784497

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6ea7dc05f496'
down_revision = 'fbc7cf864b24'
branch_labels = None
depends_on = None

history_table = sa.sql.table('history',
                             sa.Column('detail', sa.Text),
                             )


def upgrade():
    op.execute(
        history_table.update()
            .where(history_table.c.detail.like('%"add_rrests":%'))
            .values({
                'detail': sa.func.replace(
                                sa.func.replace(history_table.c.detail, '"add_rrests":', '"add_rrsets":'),
                                '"del_rrests":', '"del_rrsets":'
                          )
            })
    )


def downgrade():
    op.execute(
        history_table.update()
            .where(history_table.c.detail.like('%"add_rrsets":%'))
            .values({
                'detail': sa.func.replace(
                                sa.func.replace(history_table.c.detail, '"add_rrsets":', '"add_rrests":'),
                                '"del_rrsets":', '"del_rrests":'
                          )
            })
    )
