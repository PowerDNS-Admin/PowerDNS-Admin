from .base import db
from flask import current_app


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    description = db.Column(db.String(128))
    users = db.relationship('User', backref='role', lazy=True)
    apikeys = db.relationship('ApiKey', back_populates='role', lazy=True)

    def __init__(self, id=None, name=None, description=None):
        self.id = id
        self.name = name
        self.description = description

    # allow database autoincrement to do its own ID assignments
    def __init__(self, name=None, description=None):
        self.id = None
        self.name = name
        self.description = description

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

        db.session.commit()
        return {'status': True, 'msg': 'Role description updated successfully'}

    def delete_role(self, commit=True):
        """
        Delete a role
        """

        try:
            Role.query.filter(Role.name == self.name).delete()
            if commit:
                db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                'Cannot delete account {0} from DB. DETAIL: {1}'.format(
                    self.name, e))
            return False