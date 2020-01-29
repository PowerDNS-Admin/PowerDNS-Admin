from flask import current_app

from .base import db
from .user import User
from .account_user import AccountUser


class Account(db.Model):
    __tablename__ = 'account'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), index=True, unique=True, nullable=False)
    description = db.Column(db.String(128))
    contact = db.Column(db.String(128))
    mail = db.Column(db.String(128))
    domains = db.relationship("Domain", back_populates="account")

    def __init__(self, name=None, description=None, contact=None, mail=None):
        self.name = name
        self.description = description
        self.contact = contact
        self.mail = mail

        if self.name is not None:
            self.name = ''.join(c for c in self.name.lower()
                                if c in "abcdefghijklmnopqrstuvwxyz0123456789")

    def __repr__(self):
        return '<Account {0}r>'.format(self.name)

    def get_name_by_id(self, account_id):
        """
        Convert account_id to account_name
        """
        account = Account.query.filter(Account.id == account_id).first()
        if account is None:
            return ''

        return account.name

    def get_id_by_name(self, account_name):
        """
        Convert account_name to account_id
        """
        # Skip actual database lookup for empty queries
        if account_name is None or account_name == "":
            return None

        account = Account.query.filter(Account.name == account_name).first()
        if account is None:
            return None

        return account.id

    def create_account(self):
        """
        Create a new account
        """
        # Sanity check - account name
        if self.name == "":
            return {'status': False, 'msg': 'No account name specified'}

        # check that account name is not already used
        account = Account.query.filter(Account.name == self.name).first()
        if account:
            return {'status': False, 'msg': 'Account already exists'}

        db.session.add(self)
        db.session.commit()
        return {'status': True, 'msg': 'Account created successfully'}

    def update_account(self):
        """
        Update an existing account
        """
        # Sanity check - account name
        if self.name == "":
            return {'status': False, 'msg': 'No account name specified'}

        # read account and check that it exists
        account = Account.query.filter(Account.name == self.name).first()
        if not account:
            return {'status': False, 'msg': 'Account does not exist'}

        account.description = self.description
        account.contact = self.contact
        account.mail = self.mail

        db.session.commit()
        return {'status': True, 'msg': 'Account updated successfully'}

    def delete_account(self):
        """
        Delete an account
        """
        # unassociate all users first
        self.grant_privileges([])

        try:
            Account.query.filter(Account.name == self.name).delete()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                'Cannot delete account {0} from DB. DETAIL: {1}'.format(
                    self.username, e))
            return False

    def get_user(self):
        """
        Get users (id) associated with this account
        """
        user_ids = []
        query = db.session.query(
            AccountUser,
            Account).filter(User.id == AccountUser.user_id).filter(
                Account.id == AccountUser.account_id).filter(
                    Account.name == self.name).all()
        for q in query:
            user_ids.append(q[0].user_id)
        return user_ids

    def grant_privileges(self, new_user_list):
        """
        Reconfigure account_user table
        """
        account_id = self.get_id_by_name(self.name)

        account_user_ids = self.get_user()
        new_user_ids = [
            u.id
            for u in User.query.filter(User.username.in_(new_user_list)).all()
        ] if new_user_list else []

        removed_ids = list(set(account_user_ids).difference(new_user_ids))
        added_ids = list(set(new_user_ids).difference(account_user_ids))

        try:
            for uid in removed_ids:
                AccountUser.query.filter(AccountUser.user_id == uid).filter(
                    AccountUser.account_id == account_id).delete()
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                'Cannot revoke user privileges on account {0}. DETAIL: {1}'.
                format(self.name, e))

        try:
            for uid in added_ids:
                au = AccountUser(account_id, uid)
                db.session.add(au)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                'Cannot grant user privileges to account {0}. DETAIL: {1}'.
                format(self.name, e))

    def revoke_privileges_by_id(self, user_id):
        """
        Remove a single user from privilege list based on user_id
        """
        new_uids = [u for u in self.get_user() if u != user_id]
        users = []
        for uid in new_uids:
            users.append(User(id=uid).get_user_info_by_id().username)

        self.grant_privileges(users)

    def add_user(self, user):
        """
        Add a single user to Account by User
        """
        try:
            au = AccountUser(self.id, user.id)
            db.session.add(au)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                'Cannot add user privileges on account {0}. DETAIL: {1}'.
                format(self.name, e))
            return False

    def remove_user(self, user):
        """
        Remove a single user from Account by User
        """
        # TODO: This func is currently used by SAML feature in a wrong way. Fix it
        try:
            AccountUser.query.filter(AccountUser.user_id == user.id).filter(
                AccountUser.account_id == self.id).delete()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                'Cannot revoke user privileges on account {0}. DETAIL: {1}'.
                format(self.name, e))
            return False
