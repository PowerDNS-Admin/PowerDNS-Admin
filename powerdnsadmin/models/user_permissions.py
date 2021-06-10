from .base import db

class UserPermissions(db.Model):
    __tablename__ = 'user_permissions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    create_domain = db.Column(db.Boolean,default=False)
    remove_domain = db.Column(db.Boolean,default=False)
    alter_record = db.Column(db.Boolean,default=True)

    def __init__(self, id=None, user_id=None, create_domain=None, remove_domain=None, alter_record=None):
        self.id = id
        self.user_id = user_id
        self.create_domain = create_domain
        self.remove_domain = remove_domain
        self.alter_record = alter_record

    def __repr__(self):
        return '<UserPermission {0} {1}>'.format(self.id, self.user_id)

    def add(self):
        """
        Add UserPermission
        """

        up = UserPermissions()
        up.user_id = self.user_id
        up.create_domain = self.create_domain
        up.remove_domain = self.remove_domain
        up.alter_record = self.alter_record
        db.session.add(up)
        db.session.commit()

        return True

    def update(self, create_domain, remove_domain, alter_record=True):
        """
        Update UserPermission
        """

        self.create_domain = create_domain
        self.remove_domain = remove_domain
        self.alter_record = alter_record

        db.session.commit()

        return True
