from .base import db
from flask import current_app
import json
import re

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    description = db.Column(db.String(128))
    forward_access = db.Column(db.Text())  # {"type":"W or R or None string literal"}
    reverse_access = db.Column(db.Text())
    
    can_configure_dnssec = db.Column(db.Boolean())
    can_access_history = db.Column(db.Boolean())
    can_create_domain = db.Column(db.Boolean())
    can_remove_domain = db.Column(db.Boolean())
    can_edit_roles = db.Column(db.Boolean())
    can_view_edit_all_domains = db.Column(db.Boolean())
    
    users = db.relationship('User', backref='role', lazy=True)
    apikeys = db.relationship('ApiKey', back_populates='role', lazy=True)

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
    def __init__(self, id=None, name=None, description=None):
        self.id = id
        self.name = name
        self.description = description
        self.forward_access = json.dumps(self.defaults['forward_records_allow_edit'])
        self.reverse_access = json.dumps(self.defaults['reverse_records_allow_edit'])
        self.can_configure_dnssec = False
        self.can_access_history = False
        self.can_create_domain = False
        self.can_remove_domain = False
        self.can_edit_roles = False
        self.can_view_edit_all_domains = False
    # allow database autoincrement to do its own ID assignments
    def __init__(self, name=None, description=None):
        self.id = None
        self.name = name
        self.description = description
        self.forward_access = json.dumps(self.defaults['forward_records_allow_edit'])
        self.reverse_access = json.dumps(self.defaults['reverse_records_allow_edit'])
        self.can_configure_dnssec = False
        self.can_access_history = False
        self.can_create_domain = False
        self.can_remove_domain = False
        self.can_edit_roles = False
        self.can_view_edit_all_domains = False

    def __repr__(self):
        return '<Role {0}r>'.format(self.name)

    def create_role(self):
        """
        Create a new role
        """
        # Sanity check - role name
        if self.name == "":
            return {'status': False, 'msg': 'No role name specified'}

        # check that role name is not already used
        role = Role.query.filter(Role.name == self.name).first()
        if role:
            return {'status': False, 'msg': 'Role already exists'}
        db.session.add(self)
        db.session.commit()
        return {'status': True, 'msg': 'Role created successfully'}

    def get_id_by_name(self, role_name):
        """
        Convert role_name to role_id
        """
        # Skip actual database lookup for empty queries
        if role_name is None or role_name == "":
            return None

        role = Role.query.filter(Role.name == role_name).first()
        if role is None:
            return None

        return role.id

    def get_name_by_id(self, role_id):
        """
        Convert role_id to role_name
        """
        role = Role.query.filter(Role.id == role_id).first()
        if role is None:
            return ''

        return role.name
    
    def get_user(self):
        role_user_ids = []
        for u in self.users:
            role_user_ids.append(u.id)
        return role_user_ids
        
    def update_role(self):
        """
        Update an existing role
        """
        # Sanity check - role name
        if self.name == "":
            return {'status': False, 'msg': 'No role name specified'}

        # read role and check that it exists
        role = Role.query.filter(Role.name == self.name).first()
        if not role:
            return {'status': False, 'msg': 'Role does not exist'}

        role.description = self.description
        role.forward_access = self.forward_access
        role.reverse_access = self.reverse_access
        role.can_configure_dnssec = self.can_configure_dnssec
        role.can_access_history = self.can_access_history
        role.can_create_domain = self.can_create_domain
        role.can_remove_domain = self.can_remove_domain
        role.can_edit_roles = self.can_edit_roles
        role.can_view_edit_all_domains = self.can_view_edit_all_domains
        db.session.commit()
        return {'status': True, 'msg': 'Role description updated successfully'}

    def delete_role(self, commit=True):
        """
        Delete a role
        """
        from .api_key import ApiKey
        try:
            Role.query.filter(Role.name == self.name).delete()
            # when a Role is deleted, delete also all the api keys which are
            # associated with this role
            ApiKey.query.filter(self.id == ApiKey.role_id).delete()
            if commit:
                db.session.commit()
                
            return True

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                'Cannot delete account {0} from DB. DETAIL: {1}'.format(
                    self.name, e))
            return False
    
    def get_forward_records_allow_to_view_edit(self):
        records_allow_to_view = []
        records_allow_to_edit = []
        dictionary = json.loads(self.forward_access)

        for rec_type in dictionary:
            if dictionary[rec_type] == 'W':
                records_allow_to_view.append(rec_type)
                records_allow_to_edit.append(rec_type)
            elif dictionary[rec_type] == 'R':
                records_allow_to_view.append(rec_type)
        
        return records_allow_to_view, records_allow_to_edit
    
    def get_reverse_records_allow_to_view_edit(self):
        records_allow_to_view = []
        records_allow_to_edit = []
        dictionary = json.loads(self.reverse_access)

        for rec_type in dictionary:
            if dictionary[rec_type] == 'W':
                records_allow_to_view.append(rec_type)
                records_allow_to_edit.append(rec_type)
            elif dictionary[rec_type] == 'R':
                records_allow_to_view.append(rec_type)
        
        return records_allow_to_view, records_allow_to_edit

    def get_records_allow_to_view(self, domain_name):
        if not re.search(r'ip6\.arpa|in-addr\.arpa$', domain_name): # is forward
            dictionary = self.get_forward_records_allow_to_view_edit()[0]
        else:
            dictionary = self.get_reverse_records_allow_to_view_edit()[0]

        return dictionary
    
    def get_records_allow_to_edit(self, domain_name):
        if not re.search(r'ip6\.arpa|in-addr\.arpa$', domain_name): # is forward
            dictionary = self.get_forward_records_allow_to_view_edit()[1]
        else:
            dictionary = self.get_reverse_records_allow_to_view_edit()[1]

        return dictionary

    def get_records_allow_to_view_edit(self, domain_name):
        if not re.search(r'ip6\.arpa|in-addr\.arpa$', domain_name): # is forward
            dictionary = self.get_forward_records_allow_to_view_edit()
        else:
            dictionary = self.get_reverse_records_allow_to_view_edit()

        return dictionary