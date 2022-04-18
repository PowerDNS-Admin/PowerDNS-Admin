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
    connection = op.get_bind()

    meta = MetaData(bind=connection)
    meta.reflect(only=('role',))

    # Select all existing names that need migrating.
    roles = Table('role',meta)

    with op.batch_alter_table('role', schema=None) as batch_op:
        batch_op.add_column(
                      sa.Column('forward_access', sa.Text(), nullable=True))
        batch_op.add_column(
                      sa.Column('reverse_access', sa.Text(), nullable=True))
        
        batch_op.add_column(
                    sa.Column('can_configure_dnssec', sa.Boolean(), nullable=True))
        batch_op.add_column(
                    sa.Column('can_access_history', sa.Boolean(), nullable=True))
        batch_op.add_column(
                    sa.Column('can_create_domain', sa.Boolean(), nullable=True))
        batch_op.add_column(
                    sa.Column('can_remove_domain', sa.Boolean(), nullable=True))
        batch_op.add_column(
                    sa.Column('can_edit_roles', sa.Boolean(), nullable=True))
        batch_op.add_column(
                    sa.Column('can_view_edit_all_domains', sa.Boolean(), nullable=True))

    # op.execute("DELETE FROM setting WHERE name = 'allow_user_create_domain'")
    op.execute("""
    UPDATE role
    SET forward_access = '{0}', reverse_access = '{1}', can_configure_dnssec = true, can_access_history = true, can_create_domain = true, can_remove_domain = true, can_edit_roles = true, can_view_edit_all_domains = true
    WHERE role.id <= 3
    """.format(forward_records,reverse_records))

    op.execute("""
    UPDATE role
    SET can_configure_dnssec = false, can_access_history = false, can_create_domain = false, can_remove_domain = false, can_edit_roles = false, can_view_edit_all_domains = false
    WHERE role.id = 2
    """.format(forward_records,reverse_records))

def downgrade():

    op.drop_table('role')
    
    role_table = op.create_table('role',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=True),
        sa.Column('description', sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.bulk_insert(role_table,
        [
            {'id': 1, 'name': 'Administrator', 'description': 'Administrator'},
            {'id': 2, 'name': 'User', 'description': 'User'},
            {'id': 3, 'name': 'Operator', 'description': 'Operator'}
        ]
    )

    # Revert any users with custom roles to Users
    op.execute("""
    UPDATE user
    SET role_id = 2
    WHERE role_id > 3
    """)