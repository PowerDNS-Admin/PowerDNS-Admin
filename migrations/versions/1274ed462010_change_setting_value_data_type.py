"""Change setting.value data type

Revision ID: 1274ed462010
Revises: 59729e468045
Create Date: 2018-08-21 17:12:30.058782

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1274ed462010'
down_revision = '59729e468045'
branch_labels = None
depends_on = None


def update_data():
    setting_table = sa.sql.table('setting',
        sa.sql.column('id', sa.Integer),
        sa.sql.column('name', sa.String),
        sa.sql.column('value', sa.String),
        sa.sql.column('view', sa.String)
    )

    # add more new settings
    op.bulk_insert(setting_table,
        [
            {'id': 42, 'name': 'forward_records_allow_edit', 'value': "{'A': True, 'AAAA': True, 'AFSDB': False, 'ALIAS': False, 'CAA': True, 'CERT': False, 'CDNSKEY': False, 'CDS': False, 'CNAME': True, 'DNSKEY': False, 'DNAME': False, 'DS': False, 'HINFO': False, 'KEY': False, 'LOC': True, 'MX': True, 'NAPTR': False, 'NS': True, 'NSEC': False, 'NSEC3': False, 'NSEC3PARAM': False, 'OPENPGPKEY': False, 'PTR': True, 'RP': False, 'RRSIG': False, 'SOA': False, 'SPF': True, 'SSHFP': False, 'SRV': True, 'TKEY': False, 'TSIG': False, 'TLSA': False, 'SMIMEA': False, 'TXT': True, 'URI': False}", 'view': 'records'},
            {'id': 43, 'name': 'reverse_records_allow_edit', 'value': "{'A': False, 'AAAA': False, 'AFSDB': False, 'ALIAS': False, 'CAA': False, 'CERT': False, 'CDNSKEY': False, 'CDS': False, 'CNAME': False, 'DNSKEY': False, 'DNAME': False, 'DS': False, 'HINFO': False, 'KEY': False, 'LOC': True, 'MX': False, 'NAPTR': False, 'NS': True, 'NSEC': False, 'NSEC3': False, 'NSEC3PARAM': False, 'OPENPGPKEY': False, 'PTR': True, 'RP': False, 'RRSIG': False, 'SOA': False, 'SPF': False, 'SSHFP': False, 'SRV': False, 'TKEY': False, 'TSIG': False, 'TLSA': False, 'SMIMEA': False, 'TXT': True, 'URI': False}", 'view': 'records'},
        ]
    )

def upgrade():
    with op.batch_alter_table('setting') as batch_op:
        # change column data type
        batch_op.alter_column('value', existing_type=sa.String(256), type_=sa.Text())
    # update data for new schema
    update_data()


def downgrade():
    # delete added records in previous version
    op.execute("DELETE FROM setting WHERE id > 41")
    with op.batch_alter_table('setting') as batch_op:
        # change column data type
        batch_op.alter_column('value', existing_type=sa.Text(), type_=sa.String(256))
