"""initilize record access for default roles

Revision ID: 11df9ff49c0a
Revises: 0967658d9c0d
Create Date: 2022-01-12 12:45:09.848995

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Table, MetaData, or_
import json
# revision identifiers, used by Alembic.
revision = '11df9ff49c0a'
down_revision = '0967658d9c0d'
branch_labels = None
depends_on = None


defaults = {
    'forward_records_allow_edit': {
        'A': 'R',
        'AAAA': 'W',
        'AFSDB': 'None',
        'ALIAS': 'None',
        'CAA': 'W',
        'CERT': 'None',
        'CDNSKEY': 'None',
        'CDS': 'None',
        'CNAME': 'W',
        'DNSKEY': 'None',
        'DNAME': 'None',
        'DS': 'None',
        'HINFO': 'None',
        'KEY': 'None',
        'LOC': 'W',
        'LUA': 'None',
        'MX': 'W',
        'NAPTR': 'None',
        'NS': 'W',
        'NSEC': 'None',
        'NSEC3': 'None',
        'NSEC3PARAM': 'None',
        'OPENPGPKEY': 'None',
        'PTR': 'W',
        'RP': 'None',
        'RRSIG': 'None',
        'SOA': 'None',
        'SPF': 'W',
        'SSHFP': 'None',
        'SRV': 'W',
        'TKEY': 'None',
        'TSIG': 'None',
        'TLSA': 'None',
        'SMIMEA': 'None',
        'TXT': 'W',
        'URI': 'None'
    },
    'reverse_records_allow_edit': {
        'A': 'None',
        'AAAA': 'None',
        'AFSDB': 'None',
        'ALIAS': 'None',
        'CAA': 'None',
        'CERT': 'None',
        'CDNSKEY': 'None',
        'CDS': 'None',
        'CNAME': 'None',
        'DNSKEY': 'None',
        'DNAME': 'None',
        'DS': 'None',
        'HINFO': 'None',
        'KEY': 'None',
        'LOC': 'W',
        'LUA': 'None',
        'MX': 'None',
        'NAPTR': 'None',
        'NS': 'W',
        'NSEC': 'None',
        'NSEC3': 'None',
        'NSEC3PARAM': 'None',
        'OPENPGPKEY': 'None',
        'PTR': 'W',
        'RP': 'None',
        'RRSIG': 'None',
        'SOA': 'None',
        'SPF': 'None',
        'SSHFP': 'None',
        'SRV': 'None',
        'TKEY': 'None',
        'TSIG': 'None',
        'TLSA': 'None',
        'SMIMEA': 'None',
        'TXT': 'W',
        'URI': 'None'
    }
}

forward_records = json.dumps(defaults['forward_records_allow_edit'])
reverse_records = json.dumps(defaults['reverse_records_allow_edit'])

def upgrade():
    # Use Alchemy's connection and transaction to noodle over the data.
    return
    connection = op.get_bind()

    meta = MetaData(bind=connection)
    meta.reflect(only=('role',))

    # Select all existing names that need migrating.
    roles = Table('role',meta)

    op.add_column('role',
                  sa.Column('forward_access', sa.Text(), nullable=True))
    op.add_column('role',
                  sa.Column('reverse_access', sa.Text(), nullable=True))

    results = connection.execute(
        sa.select([roles]).where(or_(
            roles.columns.name == 'Administrator',
            roles.columns.name == 'Operator',
            roles.columns.name == 'User'
    ))).fetchall()

    # op.execute("DELETE FROM setting WHERE name = 'allow_user_create_domain'")
    op.execute("""
    UPDATE role
    SET forward_access = '{0}', reverse_access = '{1}'
    WHERE role.id <= 3
    """.format(forward_records,reverse_records))


def downgrade():

    # op.drop_column('role', 'forward_access')
    # op.drop_column('role', 'reverse_access')
    # op.execute("DROP COLUMN ")
    pass