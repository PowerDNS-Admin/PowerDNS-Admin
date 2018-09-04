"""Adding Operator Role

Revision ID: 4a666113c7bb
Revises: 1274ed462010
Create Date: 2018-08-30 13:28:06.836208

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a666113c7bb'
down_revision = '1274ed462010'
branch_labels = None
depends_on = None


def update_data():
    setting_table = sa.sql.table('setting',
        sa.sql.column('id', sa.Integer),
        sa.sql.column('name', sa.String),
        sa.sql.column('value', sa.String),
        sa.sql.column('view', sa.String)
    )

    # add new settings
    op.bulk_insert(setting_table,
        [
            {'id': 44, 'name': 'ldap_operator_group', 'value': '', 'view': 'authentication'},
            {'id': 45, 'name': 'allow_user_create_domain', 'value': 'False', 'view': 'basic'},
            {'id': 46, 'name': 'record_quick_edit', 'value': 'True', 'view': 'basic'},
        ]
    )

    role_table = sa.sql.table('role',
        sa.sql.column('id', sa.Integer),
        sa.sql.column('name', sa.String),
        sa.sql.column('description', sa.String)
    )

    # add new role
    op.bulk_insert(role_table,
        [
            {'id': 3, 'name': 'Operator', 'description': 'Operator'}
        ]
    )


def upgrade():
    update_data()


def downgrade():
    # remove user Operator role
    op.execute("UPDATE user SET role_id = 2 WHERE role_id=3")
    op.execute("DELETE FROM role WHERE name = 'Operator'")

    # delete settings
    op.execute("DELETE FROM setting WHERE name = 'ldap_operator_group'")
    op.execute("DELETE FROM setting WHERE name = 'allow_user_create_domain'")
