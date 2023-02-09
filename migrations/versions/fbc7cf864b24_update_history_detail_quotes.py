"""update history detail quotes

Revision ID: fbc7cf864b24
Revises: 0967658d9c0d
Create Date: 2022-05-04 19:49:54.054285

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fbc7cf864b24'
down_revision = '0967658d9c0d'
branch_labels = None
depends_on = None


def upgrade():
    history_table = sa.sql.table(
        'history',
        sa.Column('id', sa.Integer),
        sa.Column('msg', sa.String),
        sa.Column('detail', sa.Text),
        sa.Column('created_by', sa.String),
        sa.Column('created_on', sa.DateTime),
        sa.Column('domain_id', sa.Integer)
    )

    op.execute(
        history_table.update().where(
            sa.and_(
                history_table.c.detail.like("%'%"),
                history_table.c.detail.notlike("%rrests%"),
                history_table.c.detail.notlike("%rrsets%")
            )
        ).values({
            'detail': sa.func.replace(
                history_table.c.detail,
                "'",
                '"'
            )
        })
    )


def downgrade():
    pass
