import sys
import os
import re
import ldap
import ldap.filter
import base64
import bcrypt
import itertools
import traceback
import pyotp
import dns.reversename
import dns.inet
import dns.name
import pytimeparse
import random
import string

from ast import literal_eval
from datetime import datetime
from urllib.parse import urljoin
from distutils.util import strtobool
from distutils.version import StrictVersion
from flask_login import AnonymousUserMixin
from app import db, app
from app.lib import utils
from app.lib.log import logging


class Anonymous(AnonymousUserMixin):

    def __init__(self):
        self.username = 'Anonymous'


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password = db.Column(db.String(64))
    firstname = db.Column(db.String(64))
    lastname = db.Column(db.String(64))
    email = db.Column(db.String(128))
    avatar = db.Column(db.String(128))
    otp_secret = db.Column(db.String(16))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    def __init__(self, id=None, username=None, password=None, plain_text_password=None, firstname=None, lastname=None, role_id=None, email=None, avatar=None, otp_secret=None, reload_info=True):
        self.id = id
        self.username = username
        self.password = password
        self.plain_text_password = plain_text_password
        self.firstname = firstname
        self.lastname = lastname
        self.role_id = role_id
        self.email = email
        self.avatar = avatar
        self.otp_secret = otp_secret

        if reload_info:
            user_info = self.get_user_info_by_id() if id else self.get_user_info_by_username()

            if user_info:
                self.id = user_info.id
                self.username = user_info.username
                self.firstname = user_info.firstname
                self.lastname = user_info.lastname
                self.email = user_info.email
                self.role_id = user_info.role_id
                self.otp_secret = user_info.otp_secret

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def __repr__(self):
        return '<User {0}>'.format(self.username)

    def get_totp_uri(self):
        return "otpauth://totp/PowerDNS-Admin:{0}?secret={1}&issuer=PowerDNS-Admin".format(self.username, self.otp_secret)

    def verify_totp(self, token):
        totp = pyotp.TOTP(self.otp_secret)
        return totp.verify(token)

    def get_hashed_password(self, plain_text_password=None):
        # Hash a password for the first time
        #   (Using bcrypt, the salt is saved into the hash itself)
        if plain_text_password is None:
            return plain_text_password

        pw = plain_text_password if plain_text_password else self.plain_text_password
        return bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())

    def check_password(self, hashed_password):
        # Check hased password. Using bcrypt, the salt is saved into the hash itself
        if (self.plain_text_password):
            return bcrypt.checkpw(self.plain_text_password.encode('utf-8'), hashed_password.encode('utf-8'))
        return False

    def get_user_info_by_id(self):
        user_info = User.query.get(int(self.id))
        return user_info

    def get_user_info_by_username(self):
        user_info = User.query.filter(User.username == self.username).first()
        return user_info

    def ldap_init_conn(self):
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        conn = ldap.initialize(Setting().get('ldap_uri'))
        conn.set_option(ldap.OPT_REFERRALS, ldap.OPT_OFF)
        conn.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
        conn.set_option(ldap.OPT_X_TLS, ldap.OPT_X_TLS_DEMAND)
        conn.set_option(ldap.OPT_X_TLS_DEMAND, True)
        conn.set_option(ldap.OPT_DEBUG_LEVEL, 255)
        conn.protocol_version = ldap.VERSION3
        return conn

    def ldap_search(self, searchFilter, baseDN):
        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = None

        try:
            conn = self.ldap_init_conn()
            if Setting().get('ldap_type') == 'ad':
                conn.simple_bind_s(
                    "{0}@{1}".format(self.username, Setting().get('ldap_domain')), self.password)
            else:
                conn.simple_bind_s(
                    Setting().get('ldap_admin_username'), Setting().get('ldap_admin_password'))
            ldap_result_id = conn.search(baseDN, searchScope, searchFilter, retrieveAttributes)
            result_set = []

            while 1:
                result_type, result_data = conn.result(ldap_result_id, 0)
                if (result_data == []):
                    break
                else:
                    if result_type == ldap.RES_SEARCH_ENTRY:
                        result_set.append(result_data)
            return result_set

        except ldap.LDAPError as e:
            logging.error(e)
            logging.debug('baseDN: {0}'.format(baseDN))
            logging.debug(traceback.format_exc())

    def ldap_auth(self, ldap_username, password):
        try:
            conn = self.ldap_init_conn()
            conn.simple_bind_s(ldap_username, password)
            return True
        except ldap.LDAPError as e:
            logging.error(e)
            return False

    def ad_recursive_groups(self, groupDN):
        """
        Recursively list groups belonging to a group. It will allow checking deep in the Active Directory
        whether a user is allowed to enter or not
        """
        LDAP_BASE_DN = Setting().get('ldap_base_dn')
        groupSearchFilter = "(&(objectcategory=group)(member=%s))" % groupDN
        result = [groupDN]
        try:
            groups = self.ldap_search(groupSearchFilter, LDAP_BASE_DN)
            for group in groups:
                result += [group[0][0]]
                if 'memberOf' in group[0][1]:
                    for member in group[0][1]['memberOf']:
                        result += self.ad_recursive_groups(member.decode("utf-8"))
            return result
        except ldap.LDAPError as e:
            logging.exception("Recursive AD Group search error")
            return result

    def is_validate(self, method, src_ip=''):
        """
        Validate user credential
        """
        role_name = 'User'

        if method == 'LOCAL':
            user_info = User.query.filter(User.username == self.username).first()

            if user_info:
                if user_info.password and self.check_password(user_info.password):
                    logging.info(
                        'User "{0}" logged in successfully. Authentication request from {1}'.format(self.username, src_ip))
                    return True
                logging.error(
                    'User "{0}" inputted a wrong password. Authentication request from {1}'.format(self.username, src_ip))
                return False

            logging.warning(
                'User "{0}" does not exist. Authentication request from {1}'.format(self.username, src_ip))
            return False

        if method == 'LDAP':
            LDAP_TYPE = Setting().get('ldap_type')
            LDAP_BASE_DN = Setting().get('ldap_base_dn')
            LDAP_FILTER_BASIC = Setting().get('ldap_filter_basic')
            LDAP_FILTER_USERNAME = Setting().get('ldap_filter_username')
            LDAP_ADMIN_GROUP = Setting().get('ldap_admin_group')
            LDAP_OPERATOR_GROUP = Setting().get('ldap_operator_group')
            LDAP_USER_GROUP = Setting().get('ldap_user_group')
            LDAP_GROUP_SECURITY_ENABLED = Setting().get('ldap_sg_enabled')

            # validate AD user password
            if Setting().get('ldap_type') == 'ad':
                ldap_username = "{0}@{1}".format(self.username, Setting().get('ldap_domain'))
                if not self.ldap_auth(ldap_username, self.password):
                    logging.error(
                        'User "{0}" input a wrong LDAP password. Authentication request from {1}'.format(self.username, src_ip))
                    return False

            searchFilter = "(&({0}={1}){2})".format(
                LDAP_FILTER_USERNAME, self.username, LDAP_FILTER_BASIC)
            logging.debug('Ldap searchFilter {0}'.format(searchFilter))

            ldap_result = self.ldap_search(searchFilter, LDAP_BASE_DN)
            logging.debug('Ldap search result: {0}'.format(ldap_result))

            if not ldap_result:
                logging.warning(
                    'LDAP User "{0}" does not exist. Authentication request from {1}'.format(self.username, src_ip))
                return False
            else:
                try:
                    ldap_username = ldap.filter.escape_filter_chars(ldap_result[0][0][0])

                    if Setting().get('ldap_type') != 'ad':
                        # validate ldap user password
                        if not self.ldap_auth(ldap_username, self.password):
                            logging.error(
                                'User "{0}" input a wrong LDAP password. Authentication request from {1}'.format(self.username, src_ip))
                            return False

                    # check if LDAP_GROUP_SECURITY_ENABLED is True
                    # user can be assigned to ADMIN or USER role.
                    if LDAP_GROUP_SECURITY_ENABLED:
                        try:
                            if LDAP_TYPE == 'ldap':
                                if (self.ldap_search(searchFilter, LDAP_ADMIN_GROUP)):
                                    role_name = 'Administrator'
                                    logging.info(
                                        'User {0} is part of the "{1}" group that allows admin access to PowerDNS-Admin'.format(self.username, LDAP_ADMIN_GROUP))
                                elif (self.ldap_search(searchFilter, LDAP_OPERATOR_GROUP)):
                                    role_name = 'Operator'
                                    logging.info('User {0} is part of the "{1}" group that allows operator access to PowerDNS-Admin'.format(
                                        self.username, LDAP_OPERATOR_GROUP))
                                elif (self.ldap_search(searchFilter, LDAP_USER_GROUP)):
                                    logging.info(
                                        'User {0} is part of the "{1}" group that allows user access to PowerDNS-Admin'.format(self.username, LDAP_USER_GROUP))
                                else:
                                    logging.error('User {0} is not part of the "{1}", "{2}" or "{3}" groups that allow access to PowerDNS-Admin'.format(
                                        self.username, LDAP_ADMIN_GROUP, LDAP_OPERATOR_GROUP, LDAP_USER_GROUP))
                                    return False
                            elif LDAP_TYPE == 'ad':
                                user_ldap_groups = []
                                user_ad_member_of = ldap_result[0][0][1].get('memberOf')

                                if not user_ad_member_of:
                                    logging.error(
                                        'User {0} does not belong to any group while LDAP_GROUP_SECURITY_ENABLED is ON'.format(self.username))
                                    return False

                                for group in [g.decode("utf-8") for g in user_ad_member_of]:
                                    user_ldap_groups += self.ad_recursive_groups(group)

                                if (LDAP_ADMIN_GROUP in user_ldap_groups):
                                    role_name = 'Administrator'
                                    logging.info(
                                        'User {0} is part of the "{1}" group that allows admin access to PowerDNS-Admin'.format(self.username, LDAP_ADMIN_GROUP))
                                elif (LDAP_OPERATOR_GROUP in user_ldap_groups):
                                    role_name = 'Operator'
                                    logging.info('User {0} is part of the "{1}" group that allows operator access to PowerDNS-Admin'.format(
                                        self.username, LDAP_OPERATOR_GROUP))
                                elif (LDAP_USER_GROUP in user_ldap_groups):
                                    logging.info(
                                        'User {0} is part of the "{1}" group that allows user access to PowerDNS-Admin'.format(self.username, LDAP_USER_GROUP))
                                else:
                                    logging.error('User {0} is not part of the "{1}", "{2}" or "{3}" groups that allow access to PowerDNS-Admin'.format(
                                        self.username, LDAP_ADMIN_GROUP, LDAP_OPERATOR_GROUP, LDAP_USER_GROUP))
                                    return False
                            else:
                                logging.error('Invalid LDAP type')
                                return False
                        except Exception as e:
                            logging.error(
                                'LDAP group lookup for user "{0}" has failed. Authentication request from {1}'.format(self.username, src_ip))
                            logging.debug(traceback.format_exc())
                            return False

                except Exception as e:
                    logging.error('Wrong LDAP configuration. {0}'.format(e))
                    logging.debug(traceback.format_exc())
                    return False

            # create user if not exist in the db
            if not User.query.filter(User.username == self.username).first():
                self.firstname = self.username
                self.lastname = ''
                try:
                    # try to get user's firstname, lastname and email address from LDAP attributes
                    if LDAP_TYPE == 'ldap':
                        self.firstname = ldap_result[0][0][1]['givenName'][0].decode("utf-8")
                        self.lastname = ldap_result[0][0][1]['sn'][0].decode("utf-8")
                        self.email = ldap_result[0][0][1]['mail'][0].decode("utf-8")
                    elif LDAP_TYPE == 'ad':
                        self.firstname = ldap_result[0][0][1]['name'][0].decode("utf-8")
                        self.email = ldap_result[0][0][1]['userPrincipalName'][0].decode("utf-8")
                except Exception as e:
                    logging.warning("Reading ldap data threw an exception {0}".format(e))
                    logging.debug(traceback.format_exc())

                # first register user will be in Administrator role
                if User.query.count() == 0:
                    self.role_id = Role.query.filter_by(name='Administrator').first().id
                else:
                    self.role_id = Role.query.filter_by(name=role_name).first().id

                self.create_user()
                logging.info('Created user "{0}" in the DB'.format(self.username))

            # user already exists in database, set their role based on group membership (if enabled)
            if LDAP_GROUP_SECURITY_ENABLED:
                self.set_role(role_name)

            return True
        else:
            logging.error('Unsupported authentication method')
            return False

    def get_apikeys(self, domain_name=None):
        info = []
        apikey_query = db.session.query(ApiKey) \
            .join(Domain.apikeys) \
            .outerjoin(DomainUser, Domain.id == DomainUser.domain_id) \
            .outerjoin(Account, Domain.account_id == Account.id) \
            .outerjoin(AccountUser, Account.id == AccountUser.account_id) \
            .filter(
                db.or_(
                    DomainUser.user_id == User.id,
                    AccountUser.user_id == User.id
                )
        ) \
            .filter(User.id == self.id)

        if domain_name:
            info = apikey_query.filter(Domain.name == domain_name).all()
        else:
            info = apikey_query.all()

        return info

    def create_user(self):
        """
        If user logged in successfully via LDAP in the first time
        We will create a local user (in DB) in order to manage user
        profile such as name, roles,...
        """

        # Set an invalid password hash for non local users
        self.password = '*'

        db.session.add(self)
        db.session.commit()

    def create_local_user(self):
        """
        Create local user witch stores username / password in the DB
        """
        # check if username existed
        user = User.query.filter(User.username == self.username).first()
        if user:
            return {'status': False, 'msg': 'Username is already in use'}

        # check if email existed
        user = User.query.filter(User.email == self.email).first()
        if user:
            return {'status': False, 'msg': 'Email address is already in use'}

        # first register user will be in Administrator role
        self.role_id = Role.query.filter_by(name='User').first().id
        if User.query.count() == 0:
            self.role_id = Role.query.filter_by(name='Administrator').first().id

        self.password = self.get_hashed_password(
            self.plain_text_password) if self.plain_text_password else '*'

        if self.password and self.password != '*':
            self.password = self.password.decode("utf-8")

        db.session.add(self)
        db.session.commit()
        return {'status': True, 'msg': 'Created user successfully'}

    def update_local_user(self):
        """
        Update local user
        """
        # Sanity check - account name
        if self.username == "":
            return {'status': False, 'msg': 'No user name specified'}

        # read user and check that it exists
        user = User.query.filter(User.username == self.username).first()
        if not user:
            return {'status': False, 'msg': 'User does not exist'}

        # check if new email exists (only if changed)
        if user.email != self.email:
            checkuser = User.query.filter(User.email == self.email).first()
            if checkuser:
                return {'status': False, 'msg': 'New email address is already in use'}

        user.firstname = self.firstname
        user.lastname = self.lastname
        user.email = self.email

        # store new password hash (only if changed)
        if self.plain_text_password != "":
            user.password = self.get_hashed_password(self.plain_text_password).decode("utf-8")

        db.session.commit()
        return {'status': True, 'msg': 'User updated successfully'}

    def update_profile(self, enable_otp=None):
        """
        Update user profile
        """

        user = User.query.filter(User.username == self.username).first()
        if not user:
            return False

        user.firstname = self.firstname if self.firstname else user.firstname
        user.lastname = self.lastname if self.lastname else user.lastname
        user.email = self.email if self.email else user.email
        user.password = self.get_hashed_password(self.plain_text_password).decode(
            "utf-8") if self.plain_text_password else user.password
        user.avatar = self.avatar if self.avatar else user.avatar

        if enable_otp is not None:
            user.otp_secret = ""

        if enable_otp == True:
            # generate the opt secret key
            user.otp_secret = base64.b32encode(os.urandom(10)).decode('utf-8')

        try:
            db.session.add(user)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    def get_account_query(self):
        """
        Get query for account to which the user is associated.
        """
        return db.session.query(Account) \
            .outerjoin(AccountUser, Account.id == AccountUser.account_id) \
            .filter(AccountUser.user_id == self.id)

    def get_account(self):
        """
        Get all accounts to which the user is associated.
        """
        return self.get_account_query()

    def get_domain_query(self):
        """
        Get query for domain to which the user has access permission.
        This includes direct domain permission AND permission through
        account membership
        """
        return db.session.query(Domain) \
            .outerjoin(DomainUser, Domain.id == DomainUser.domain_id) \
            .outerjoin(Account, Domain.account_id == Account.id) \
            .outerjoin(AccountUser, Account.id == AccountUser.account_id) \
            .filter(
                db.or_(
                    DomainUser.user_id == User.id,
                    AccountUser.user_id == User.id
                )
        ) \
            .filter(User.id == self.id)

    def get_domain(self):
        """
        Get domains which user has permission to
        access
        """
        return self.get_domain_query()

    def get_domains(self):
        return self.get_domain_query().all()

    def delete(self):
        """
        Delete a user
        """
        # revoke all user privileges and account associations first
        self.revoke_privilege()
        for a in self.get_account():
            a.revoke_privileges_by_id(self.id)

        try:
            User.query.filter(User.username == self.username).delete()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logging.error('Cannot delete user {0} from DB. DETAIL: {1}'.format(self.username, e))
            return False

    def revoke_privilege(self):
        """
        Revoke all privileges from a user
        """
        user = User.query.filter(User.username == self.username).first()

        if user:
            user_id = user.id
            try:
                DomainUser.query.filter(DomainUser.user_id == user_id).delete()
                db.session.commit()
                return True
            except Exception as e:
                db.session.rollback()
                logging.error(
                    'Cannot revoke user {0} privileges. DETAIL: {1}'.format(self.username, e))
                return False
        return False

    def set_role(self, role_name):
        role = Role.query.filter(Role.name == role_name).first()
        if role:
            user = User.query.filter(User.username == self.username).first()
            user.role_id = role.id
            db.session.commit()
            return {'status': True, 'msg': 'Set user role successfully'}
        else:
            return {'status': False, 'msg': 'Role does not exist'}


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
            self.name = ''.join(
                c for c in self.name.lower() if c in "abcdefghijklmnopqrstuvwxyz0123456789")

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

    def unassociate_domains(self):
        """
        Remove associations to this account from all domains
        """
        account = Account.query.filter(Account.name == self.name).first()
        for domain in account.domains:
            Domain(name=domain.name).assoc_account(None)

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
        # unassociate all domains and users first
        self.unassociate_domains()
        self.grant_privileges([])

        try:
            Account.query.filter(Account.name == self.name).delete()
            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            logging.error('Cannot delete account {0} from DB. DETAIL: {1}'.format(self.username, e))
            return False

    def get_user(self):
        """
        Get users (id) associated with this account
        """
        user_ids = []
        query = db.session.query(AccountUser, Account).filter(User.id == AccountUser.user_id).filter(
            Account.id == AccountUser.account_id).filter(Account.name == self.name).all()
        for q in query:
            user_ids.append(q[0].user_id)
        return user_ids

    def grant_privileges(self, new_user_list):
        """
        Reconfigure account_user table
        """
        account_id = self.get_id_by_name(self.name)

        account_user_ids = self.get_user()
        new_user_ids = [u.id for u in User.query.filter(
            User.username.in_(new_user_list)).all()] if new_user_list else []

        removed_ids = list(set(account_user_ids).difference(new_user_ids))
        added_ids = list(set(new_user_ids).difference(account_user_ids))

        try:
            for uid in removed_ids:
                AccountUser.query.filter(AccountUser.user_id == uid).filter(
                    AccountUser.account_id == account_id).delete()
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            logging.error(
                'Cannot revoke user privileges on account {0}. DETAIL: {1}'.format(self.name, e))

        try:
            for uid in added_ids:
                au = AccountUser(account_id, uid)
                db.session.add(au)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            logging.error(
                'Cannot grant user privileges to account {0}. DETAIL: {1}'.format(self.name, e))

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
            logging.error(
                'Cannot add user privileges on account {0}. DETAIL: {1}'.format(self.name, e))
            return False

    def remove_user(self, user):
        """
        Remove a single user from Account by User
        """
        try:
            AccountUser.query.filter(AccountUser.user_id == user.id).filter(
                AccountUser.account_id == self.id).delete()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logging.error(
                'Cannot revoke user privileges on account {0}. DETAIL: {1}'.format(self.name, e))
            return False


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


class DomainSetting(db.Model):
    __tablename__ = 'domain_setting'
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'))
    domain = db.relationship('Domain', back_populates='settings')
    setting = db.Column(db.String(255), nullable=False)
    value = db.Column(db.String(255))

    def __init__(self, id=None, setting=None, value=None):
        self.id = id
        self.setting = setting
        self.value = value

    def __repr__(self):
        return '<DomainSetting {0} for {1}>'.format(setting, self.domain.name)

    def __eq__(self, other):
        return type(self) == type(other) and self.setting == other.setting

    def set(self, value):
        try:
            self.value = value
            db.session.commit()
            return True
        except Exception as e:
            logging.error('Unable to set DomainSetting value. DETAIL: {0}'.format(e))
            logging.debug(traceback.format_exc())
            db.session.rollback()
            return False

domain_apikey = db.Table('domain_apikey',
    db.Column('domain_id', db.Integer, db.ForeignKey('domain.id')),
    db.Column('apikey_id', db.Integer, db.ForeignKey('apikey.id'))
)


class Domain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True, unique=True)
    master = db.Column(db.String(128))
    type = db.Column(db.String(6), nullable=False)
    serial = db.Column(db.Integer)
    notified_serial = db.Column(db.Integer)
    last_check = db.Column(db.Integer)
    dnssec = db.Column(db.Integer)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    account = db.relationship("Account", back_populates="domains")
    settings = db.relationship('DomainSetting', back_populates='domain')
    apikeys = db.relationship(
        "ApiKey",
        secondary=domain_apikey,
        back_populates="domains"
    )

    def __init__(self, id=None, name=None, master=None, type='NATIVE', serial=None, notified_serial=None, last_check=None, dnssec=None, account_id=None):
        self.id = id
        self.name = name
        self.master = master
        self.type = type
        self.serial = serial
        self.notified_serial = notified_serial
        self.last_check = last_check
        self.dnssec = dnssec
        self.account_id = account_id
        # PDNS configs
        self.PDNS_STATS_URL = Setting().get('pdns_api_url')
        self.PDNS_API_KEY = Setting().get('pdns_api_key')
        self.PDNS_VERSION = Setting().get('pdns_version')
        self.API_EXTENDED_URL = utils.pdns_api_extended_uri(self.PDNS_VERSION)

        if StrictVersion(self.PDNS_VERSION) >= StrictVersion('4.0.0'):
            self.NEW_SCHEMA = True
        else:
            self.NEW_SCHEMA = False

    def __repr__(self):
        return '<Domain {0}>'.format(self.name)

    def add_setting(self, setting, value):
        try:
            self.settings.append(DomainSetting(setting=setting, value=value))
            db.session.commit()
            return True
        except Exception as e:
            logging.error(
                'Can not create setting {0} for domain {1}. {2}'.format(setting, self.name, e))
            return False

    def get_domain_info(self, domain_name):
        """
        Get all domains which has in PowerDNS
        """
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY
        jdata = utils.fetch_json(
            urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL + '/servers/localhost/zones/{0}'.format(domain_name)), headers=headers)
        return jdata

    def get_domains(self):
        """
        Get all domains which has in PowerDNS
        """
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY
        jdata = utils.fetch_json(
            urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL + '/servers/localhost/zones'), headers=headers)
        return jdata

    def get_id_by_name(self, name):
        """
        Return domain id
        """
        try:
            domain = Domain.query.filter(Domain.name == name).first()
            return domain.id
        except Exception as e:
            logging.error('Domain does not exist. ERROR: {0}'.format(e))
            return None

    def update(self):
        """
        Fetch zones (domains) from PowerDNS and update into DB
        """
        db_domain = Domain.query.all()
        list_db_domain = [d.name for d in db_domain]
        dict_db_domain = dict((x.name, x) for x in db_domain)

        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY
        try:
            jdata = utils.fetch_json(
                urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL + '/servers/localhost/zones'), headers=headers)
            list_jdomain = [d['name'].rstrip('.') for d in jdata]
            try:
                # domains should remove from db since it doesn't exist in powerdns anymore
                should_removed_db_domain = list(set(list_db_domain).difference(list_jdomain))
                for d in should_removed_db_domain:
                    # revoke permission before delete domain
                    domain = Domain.query.filter(Domain.name == d).first()
                    domain_user = DomainUser.query.filter(DomainUser.domain_id == domain.id)
                    if domain_user:
                        domain_user.delete()
                        db.session.commit()
                    domain_setting = DomainSetting.query.filter(
                        DomainSetting.domain_id == domain.id)
                    if domain_setting:
                        domain_setting.delete()
                        db.session.commit()

                    domain.apikeys[:] = []
                    db.session.commit()

                    # then remove domain
                    Domain.query.filter(Domain.name == d).delete()
                    db.session.commit()
            except Exception as e:
                logging.error('Can not delete domain from DB. DETAIL: {0}'.format(e))
                logging.debug(traceback.format_exc())
                db.session.rollback()

            # update/add new domain
            for data in jdata:
                if 'account' in data:
                    account_id = Account().get_id_by_name(data['account'])
                else:
                    logging.debug(
                        "No 'account' data found in API result - Unsupported PowerDNS version?")
                    account_id = None
                d = dict_db_domain.get(data['name'].rstrip('.'), None)
                changed = False
                if d:
                    # existing domain, only update if something actually has changed
                    if (d.master != str(data['masters'])
                        or d.type != data['kind']
                        or d.serial != data['serial']
                        or d.notified_serial != data['notified_serial']
                        or d.last_check != (1 if data['last_check'] else 0)
                        or d.dnssec != data['dnssec']
                        or d.account_id != account_id):

                        d.master = str(data['masters'])
                        d.type = data['kind']
                        d.serial = data['serial']
                        d.notified_serial = data['notified_serial']
                        d.last_check = 1 if data['last_check'] else 0
                        d.dnssec = 1 if data['dnssec'] else 0
                        d.account_id = account_id
                        changed = True

                else:
                    # add new domain
                    d = Domain()
                    d.name = data['name'].rstrip('.')
                    d.master = str(data['masters'])
                    d.type = data['kind']
                    d.serial = data['serial']
                    d.notified_serial = data['notified_serial']
                    d.last_check = data['last_check']
                    d.dnssec = 1 if data['dnssec'] else 0
                    d.account_id = account_id
                    db.session.add(d)
                    changed = True
                if changed:
                    try:
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
            return {'status': 'ok', 'msg': 'Domain table has been updated successfully'}
        except Exception as e:
            logging.error('Can not update domain table. Error: {0}'.format(e))
            return {'status': 'error', 'msg': 'Can not update domain table'}

    def add(self, domain_name, domain_type, soa_edit_api, domain_ns=[], domain_master_ips=[], account_name=None):
        """
        Add a domain to power dns
        """
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY

        if self.NEW_SCHEMA:
            domain_name = domain_name + '.'
            domain_ns = [ns + '.' for ns in domain_ns]

        if soa_edit_api not in ["DEFAULT", "INCREASE", "EPOCH", "OFF"]:
            soa_edit_api = 'DEFAULT'

        elif soa_edit_api == 'OFF':
            soa_edit_api = ''

        post_data = {
            "name": domain_name,
            "kind": domain_type,
            "masters": domain_master_ips,
            "nameservers": domain_ns,
            "soa_edit_api": soa_edit_api,
            "account": account_name
        }

        try:
            jdata = utils.fetch_json(
                urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL + '/servers/localhost/zones'), headers=headers, method='POST', data=post_data)
            if 'error' in jdata.keys():
                logging.error(jdata['error'])
                return {'status': 'error', 'msg': jdata['error']}
            else:
                self.update()
                logging.info('Added domain {0} successfully'.format(domain_name))
                return {'status': 'ok', 'msg': 'Added domain successfully'}
        except Exception as e:
            logging.error('Cannot add domain {0}'.format(domain_name))
            logging.debug(traceback.format_exc())
            return {'status': 'error', 'msg': 'Cannot add this domain.'}

    def update_soa_setting(self, domain_name, soa_edit_api):
        domain = Domain.query.filter(Domain.name == domain_name).first()
        if not domain:
            return {'status': 'error', 'msg': 'Domain doesnt exist.'}
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY

        if soa_edit_api not in ["DEFAULT", "INCREASE", "EPOCH", "OFF"]:
            soa_edit_api = 'DEFAULT'

        elif soa_edit_api == 'OFF':
            soa_edit_api = ''

        post_data = {
            "soa_edit_api": soa_edit_api,
            "kind": domain.type
        }

        try:
            jdata = utils.fetch_json(
                urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL + '/servers/localhost/zones/{0}'.format(domain.name)), headers=headers,
                method='PUT', data=post_data)
            if 'error' in jdata.keys():
                logging.error(jdata['error'])
                return {'status': 'error', 'msg': jdata['error']}
            else:
                logging.info('soa-edit-api changed for domain {0} successfully'.format(domain_name))
                return {'status': 'ok', 'msg': 'soa-edit-api changed successfully'}
        except Exception as e:
            logging.debug(e)
            logging.debug(traceback.format_exc())
            logging.error('Cannot change soa-edit-api for domain {0}'.format(domain_name))
            return {'status': 'error', 'msg': 'Cannot change soa-edit-api this domain.'}

    def create_reverse_domain(self, domain_name, domain_reverse_name):
        """
        Check the existing reverse lookup domain,
        if not exists create a new one automatically
        """
        domain_obj = Domain.query.filter(Domain.name == domain_name).first()
        domain_auto_ptr = DomainSetting.query.filter(
            DomainSetting.domain == domain_obj).filter(DomainSetting.setting == 'auto_ptr').first()
        domain_auto_ptr = strtobool(domain_auto_ptr.value) if domain_auto_ptr else False
        system_auto_ptr = Setting().get('auto_ptr')
        self.name = domain_name
        domain_id = self.get_id_by_name(domain_reverse_name)
        if None == domain_id and \
            (
                system_auto_ptr or
                domain_auto_ptr
            ):
            result = self.add(domain_reverse_name, 'Master', 'DEFAULT', '', '')
            self.update()
            if result['status'] == 'ok':
                history = History(msg='Add reverse lookup domain {0}'.format(domain_reverse_name), detail=str(
                    {'domain_type': 'Master', 'domain_master_ips': ''}), created_by='System')
                history.add()
            else:
                return {'status': 'error', 'msg': 'Adding reverse lookup domain failed'}
            domain_user_ids = self.get_user()
            domain_users = []
            u = User()
            for uid in domain_user_ids:
                u.id = uid
                tmp = u.get_user_info_by_id()
                domain_users.append(tmp.username)
            if 0 != len(domain_users):
                self.name = domain_reverse_name
                self.grant_privileges(domain_users)
                return {'status': 'ok', 'msg': 'New reverse lookup domain created with granted privileges'}
            return {'status': 'ok', 'msg': 'New reverse lookup domain created without users'}
        return {'status': 'ok', 'msg': 'Reverse lookup domain already exists'}

    def get_reverse_domain_name(self, reverse_host_address):
        c = 1
        if re.search('ip6.arpa', reverse_host_address):
            for i in range(1, 32, 1):
                address = re.search(
                    '((([a-f0-9]\.){' + str(i) + '})(?P<ipname>.+6.arpa)\.?)', reverse_host_address)
                if None != self.get_id_by_name(address.group('ipname')):
                    c = i
                    break
            return re.search('((([a-f0-9]\.){' + str(c) + '})(?P<ipname>.+6.arpa)\.?)', reverse_host_address).group('ipname')
        else:
            for i in range(1, 4, 1):
                address = re.search(
                    '((([0-9]+\.){' + str(i) + '})(?P<ipname>.+r.arpa)\.?)', reverse_host_address)
                if None != self.get_id_by_name(address.group('ipname')):
                    c = i
                    break
            return re.search('((([0-9]+\.){' + str(c) + '})(?P<ipname>.+r.arpa)\.?)', reverse_host_address).group('ipname')

    def delete(self, domain_name):
        """
        Delete a single domain name from powerdns
        """
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY
        try:
            utils.fetch_json(urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                             '/servers/localhost/zones/{0}'.format(domain_name)), headers=headers, method='DELETE')
            logging.info('Delete domain {0} successfully'.format(domain_name))
            return {'status': 'ok', 'msg': 'Delete domain successfully'}
        except Exception as e:
            logging.error('Cannot delete domain {0}'.format(domain_name))
            logging.debug(traceback.format_exc())
            return {'status': 'error', 'msg': 'Cannot delete domain'}

    def get_user(self):
        """
        Get users (id) who have access to this domain name
        """
        user_ids = []
        query = db.session.query(DomainUser, Domain).filter(User.id == DomainUser.user_id).filter(
            Domain.id == DomainUser.domain_id).filter(Domain.name == self.name).all()
        for q in query:
            user_ids.append(q[0].user_id)
        return user_ids

    def grant_privileges(self, new_user_list):
        """
        Reconfigure domain_user table
        """

        domain_id = self.get_id_by_name(self.name)

        domain_user_ids = self.get_user()
        new_user_ids = [u.id for u in User.query.filter(
            User.username.in_(new_user_list)).all()] if new_user_list else []

        removed_ids = list(set(domain_user_ids).difference(new_user_ids))
        added_ids = list(set(new_user_ids).difference(domain_user_ids))

        try:
            for uid in removed_ids:
                DomainUser.query.filter(DomainUser.user_id == uid).filter(
                    DomainUser.domain_id == domain_id).delete()
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            logging.error(
                'Cannot revoke user privileges on domain {0}. DETAIL: {1}'.format(self.name, e))

        try:
            for uid in added_ids:
                du = DomainUser(domain_id, uid)
                db.session.add(du)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            logging.error(
                'Cannot grant user privileges to domain {0}. DETAIL: {1}'.format(self.name, e))

    def update_from_master(self, domain_name):
        """
        Update records from Master DNS server
        """
        domain = Domain.query.filter(Domain.name == domain_name).first()
        if domain:
            headers = {}
            headers['X-API-Key'] = self.PDNS_API_KEY
            try:
                utils.fetch_json(
                    urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL + '/servers/localhost/zones/{0}/axfr-retrieve'.format(domain.name)), headers=headers, method='PUT')
                return {'status': 'ok', 'msg': 'Update from Master successfully'}
            except Exception as e:
                logging.error('Cannot update from master. DETAIL: {0}'.format(e))
                return {'status': 'error', 'msg': 'There was something wrong, please contact administrator'}
        else:
            return {'status': 'error', 'msg': 'This domain doesnot exist'}

    def get_domain_dnssec(self, domain_name):
        """
        Get domain DNSSEC information
        """
        domain = Domain.query.filter(Domain.name == domain_name).first()
        if domain:
            headers = {}
            headers['X-API-Key'] = self.PDNS_API_KEY
            try:
                jdata = utils.fetch_json(
                    urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL + '/servers/localhost/zones/{0}/cryptokeys'.format(domain.name)), headers=headers, method='GET')
                if 'error' in jdata:
                    return {'status': 'error', 'msg': 'DNSSEC is not enabled for this domain'}
                else:
                    return {'status': 'ok', 'dnssec': jdata}
            except Exception as e:
                logging.error('Cannot get domain dnssec. DETAIL: {0}'.format(e))
                return {'status': 'error', 'msg': 'There was something wrong, please contact administrator'}
        else:
            return {'status': 'error', 'msg': 'This domain doesnot exist'}

    def enable_domain_dnssec(self, domain_name):
        """
        Enable domain DNSSEC
        """
        domain = Domain.query.filter(Domain.name == domain_name).first()
        if domain:
            headers = {}
            headers['X-API-Key'] = self.PDNS_API_KEY
            try:
                # Enable API-RECTIFY for domain, BEFORE activating DNSSEC
                post_data = {
                    "api_rectify": True
                }
                jdata = utils.fetch_json(
                    urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL + '/servers/localhost/zones/{0}'.format(domain.name)), headers=headers, method='PUT', data=post_data)
                if 'error' in jdata:
                    return {'status': 'error', 'msg': 'API-RECTIFY could not be enabled for this domain', 'jdata': jdata}

                # Activate DNSSEC
                post_data = {
                    "keytype": "ksk",
                    "active": True
                }
                jdata = utils.fetch_json(
                    urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL + '/servers/localhost/zones/{0}/cryptokeys'.format(domain.name)), headers=headers, method='POST', data=post_data)
                if 'error' in jdata:
                    return {'status': 'error', 'msg': 'Cannot enable DNSSEC for this domain. Error: {0}'.format(jdata['error']), 'jdata': jdata}

                return {'status': 'ok'}

            except Exception as e:
                logging.error('Cannot enable dns sec. DETAIL: {}'.format(e))
                logging.debug(traceback.format_exc())
                return {'status': 'error', 'msg': 'There was something wrong, please contact administrator'}

        else:
            return {'status': 'error', 'msg': 'This domain does not exist'}

    def delete_dnssec_key(self, domain_name, key_id):
        """
        Remove keys DNSSEC
        """
        domain = Domain.query.filter(Domain.name == domain_name).first()
        if domain:
            headers = {}
            headers['X-API-Key'] = self.PDNS_API_KEY
            try:
                # Deactivate DNSSEC
                jdata = utils.fetch_json(
                    urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL + '/servers/localhost/zones/{0}/cryptokeys/{1}'.format(domain.name, key_id)), headers=headers, method='DELETE')
                if jdata != True:
                    return {'status': 'error', 'msg': 'Cannot disable DNSSEC for this domain. Error: {0}'.format(jdata['error']), 'jdata': jdata}

                # Disable API-RECTIFY for domain, AFTER deactivating DNSSEC
                post_data = {
                    "api_rectify": False
                }
                jdata = utils.fetch_json(
                    urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL + '/servers/localhost/zones/{0}'.format(domain.name)), headers=headers, method='PUT', data=post_data)
                if 'error' in jdata:
                    return {'status': 'error', 'msg': 'API-RECTIFY could not be disabled for this domain', 'jdata': jdata}

                return {'status': 'ok'}

            except Exception as e:
                logging.error('Cannot delete dnssec key. DETAIL: {0}'.format(e))
                logging.debug(traceback.format_exc())
                return {'status': 'error', 'msg': 'There was something wrong, please contact administrator', 'domain': domain.name, 'id': key_id}

        else:
            return {'status': 'error', 'msg': 'This domain doesnot exist'}

    def assoc_account(self, account_id):
        """
        Associate domain with a domain, specified by account id
        """
        domain_name = self.name

        # Sanity check - domain name
        if domain_name == "":
            return {'status': False, 'msg': 'No domain name specified'}

        # read domain and check that it exists
        domain = Domain.query.filter(Domain.name == domain_name).first()
        if not domain:
            return {'status': False, 'msg': 'Domain does not exist'}

        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY

        account_name = Account().get_name_by_id(account_id)

        post_data = {
            "account": account_name
        }

        try:
            jdata = utils.fetch_json(
                urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL + '/servers/localhost/zones/{0}'.format(domain_name)), headers=headers,
                method='PUT', data=post_data)

            if 'error' in jdata.keys():
                logging.error(jdata['error'])
                return {'status': 'error', 'msg': jdata['error']}
            else:
                self.update()
                msg_str = 'Account changed for domain {0} successfully'
                logging.info(msg_str.format(domain_name))
                return {'status': 'ok', 'msg': 'account changed successfully'}

        except Exception as e:
            logging.debug(e)
            logging.debug(traceback.format_exc())
            msg_str = 'Cannot change account for domain {0}'
            logging.error(msg_str.format(domain_name))
            return {
                    'status': 'error',
                    'msg': 'Cannot change account for this domain.'
            }

    def get_account(self):
        """
        Get current account associated with this domain
        """
        domain = Domain.query.filter(Domain.name == self.name).first()

        return domain.account


class DomainUser(db.Model):
    __tablename__ = 'domain_user'
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, domain_id, user_id):
        self.domain_id = domain_id
        self.user_id = user_id

    def __repr__(self):
        return '<Domain_User {0} {1}>'.format(self.domain_id, self.user_id)


class AccountUser(db.Model):
    __tablename__ = 'account_user'
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, account_id, user_id):
        self.account_id = account_id
        self.user_id = user_id

    def __repr__(self):
        return '<Account_User {0} {1}>'.format(self.account_id, self.user_id)


class Record(object):

    """
    This is not a model, it's just an object
    which be assigned data from PowerDNS API
    """

    def __init__(self, name=None, type=None, status=None, ttl=None, data=None):
        self.name = name
        self.type = type
        self.status = status
        self.ttl = ttl
        self.data = data
        # PDNS configs
        self.PDNS_STATS_URL = Setting().get('pdns_api_url')
        self.PDNS_API_KEY = Setting().get('pdns_api_key')
        self.PDNS_VERSION = Setting().get('pdns_version')
        self.API_EXTENDED_URL = utils.pdns_api_extended_uri(self.PDNS_VERSION)
        self.PRETTY_IPV6_PTR = Setting().get('pretty_ipv6_ptr')

        if StrictVersion(self.PDNS_VERSION) >= StrictVersion('4.0.0'):
            self.NEW_SCHEMA = True
        else:
            self.NEW_SCHEMA = False

    def get_record_data(self, domain):
        """
        Query domain's DNS records via API
        """
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY
        try:
            jdata = utils.fetch_json(
                urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL + '/servers/localhost/zones/{0}'.format(domain)), headers=headers)
        except Exception as e:
            logging.error(
                "Cannot fetch domain's record data from remote powerdns api. DETAIL: {0}".format(e))
            return False

        if self.NEW_SCHEMA:
            rrsets = jdata['rrsets']
            for rrset in rrsets:
                r_name = rrset['name'].rstrip('.')
                if self.PRETTY_IPV6_PTR:  # only if activated
                    if rrset['type'] == 'PTR':  # only ptr
                        if 'ip6.arpa' in r_name:  # only if v6-ptr
                            r_name = dns.reversename.to_address(dns.name.from_text(r_name))

                rrset['name'] = r_name
                rrset['content'] = rrset['records'][0]['content']
                rrset['disabled'] = rrset['records'][0]['disabled']
            return {'records': rrsets}

        return jdata

    def add(self, domain):
        """
        Add a record to domain
        """
        # validate record first
        r = self.get_record_data(domain)
        records = r['records']
        check = list(filter(lambda check: check['name'] == self.name, records))
        if check:
            r = check[0]
            if r['type'] in ('A', 'AAAA', 'CNAME'):
                return {'status': 'error', 'msg': 'Record already exists with type "A", "AAAA" or "CNAME"'}

        # continue if the record is ready to be added
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY

        if self.NEW_SCHEMA:
            data = {"rrsets": [
                        {
                            "name": self.name.rstrip('.') + '.',
                            "type": self.type,
                            "changetype": "REPLACE",
                            "ttl": self.ttl,
                            "records": [
                                {
                                    "content": self.data,
                                    "disabled": self.status,
                                }
                            ]
                        }
                    ]
                    }
        else:
            data = {"rrsets": [
                        {
                            "name": self.name,
                            "type": self.type,
                            "changetype": "REPLACE",
                            "records": [
                                {
                                    "content": self.data,
                                    "disabled": self.status,
                                    "name": self.name,
                                    "ttl": self.ttl,
                                    "type": self.type
                                }
                            ]
                        }
                    ]
                    }

        try:
            jdata = utils.fetch_json(
                urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL + '/servers/localhost/zones/{0}'.format(domain)), headers=headers, method='PATCH', data=data)
            logging.debug(jdata)
            return {'status': 'ok', 'msg': 'Record was added successfully'}
        except Exception as e:
            logging.error("Cannot add record {0}/{1}/{2} to domain {3}. DETAIL: {4}".format(
                self.name, self.type, self.data, domain, e))
            return {'status': 'error', 'msg': 'There was something wrong, please contact administrator'}

    def compare(self, domain_name, new_records):
        """
        Compare new records with current powerdns record data
        Input is a list of hashes (records)
        """
        # get list of current records we have in powerdns
        current_records = self.get_record_data(domain_name)['records']

        # convert them to list of list (just has [name, type]) instead of list of hash
        # to compare easier
        list_current_records = [[x['name'], x['type']] for x in current_records]
        list_new_records = [[x['name'], x['type']] for x in new_records]

        # get list of deleted records
        # they are the records which exist in list_current_records but not in list_new_records
        list_deleted_records = [x for x in list_current_records if x not in list_new_records]

        # convert back to list of hash
        deleted_records = [x for x in current_records if [x['name'], x['type']] in list_deleted_records and (
            x['type'] in Setting().get_records_allow_to_edit() and x['type'] != 'SOA')]

        # return a tuple
        return deleted_records, new_records

    def apply(self, domain, post_records):
        """
        Apply record changes to domain
        """
        records = []
        for r in post_records:
            r_name = domain if r['record_name'] in ['@', ''] else r['record_name'] + '.' + domain
            r_type = r['record_type']
            if self.PRETTY_IPV6_PTR:  # only if activated
                if self.NEW_SCHEMA:  # only if new schema
                    if r_type == 'PTR':  # only ptr
                        if ':' in r['record_name']:  # dirty ipv6 check
                            r_name = r['record_name']

            r_data = domain if r_type == 'CNAME' and r[
                'record_data'] in ['@', ''] else r['record_data']

            record = {
                        "name": r_name,
                        "type": r_type,
                        "content": r_data,
                        "disabled": True if r['record_status'] == 'Disabled' else False,
                        "ttl": int(r['record_ttl']) if r['record_ttl'] else 3600,
                    }
            records.append(record)

        deleted_records, new_records = self.compare(domain, records)

        records = []
        for r in deleted_records:
            r_name = r['name'].rstrip('.') + '.' if self.NEW_SCHEMA else r['name']
            r_type = r['type']
            if self.PRETTY_IPV6_PTR:  # only if activated
                if self.NEW_SCHEMA:  # only if new schema
                    if r_type == 'PTR':  # only ptr
                        if ':' in r['name']:  # dirty ipv6 check
                            r_name = dns.reversename.from_address(r['name']).to_text()

            record = {
                        "name": r_name,
                        "type": r_type,
                        "changetype": "DELETE",
                        "records": [
                        ]
                    }
            records.append(record)

        postdata_for_delete = {"rrsets": records}

        records = []
        for r in new_records:
            if self.NEW_SCHEMA:
                r_name = r['name'].rstrip('.') + '.'
                r_type = r['type']
                if self.PRETTY_IPV6_PTR:  # only if activated
                    if r_type == 'PTR':  # only ptr
                        if ':' in r['name']:  # dirty ipv6 check
                            r_name = r['name']

                record = {
                            "name": r_name,
                            "type": r_type,
                            "changetype": "REPLACE",
                            "ttl": r['ttl'],
                            "records": [
                                {
                                    "content": r['content'],
                                    "disabled": r['disabled'],
                                }
                            ]
                        }
            else:
                record = {
                            "name": r['name'],
                            "type": r['type'],
                            "changetype": "REPLACE",
                            "records": [
                                {
                                    "content": r['content'],
                                    "disabled": r['disabled'],
                                    "name": r['name'],
                                    "ttl": r['ttl'],
                                    "type": r['type'],
                                    "priority": 10,  # priority field for pdns 3.4.1. https://doc.powerdns.com/md/authoritative/upgrading/
                                }
                            ]
                        }

            records.append(record)

        # Adjustment to add multiple records which described in
        # https://github.com/ngoduykhanh/PowerDNS-Admin/issues/5#issuecomment-181637576
        final_records = []
        records = sorted(records, key=lambda item: (
            item["name"], item["type"], item["changetype"]))
        for key, group in itertools.groupby(records, lambda item: (item["name"], item["type"], item["changetype"])):
            if self.NEW_SCHEMA:
                r_name = key[0]
                r_type = key[1]
                r_changetype = key[2]

                if self.PRETTY_IPV6_PTR:  # only if activated
                    if r_type == 'PTR':  # only ptr
                        if ':' in r_name:  # dirty ipv6 check
                            r_name = dns.reversename.from_address(r_name).to_text()

                new_record = {
                        "name": r_name,
                        "type": r_type,
                        "changetype": r_changetype,
                        "ttl": None,
                        "records": []
                }
                for item in group:
                    temp_content = item['records'][0]['content']
                    temp_disabled = item['records'][0]['disabled']
                    if key[1] in ['MX', 'CNAME', 'SRV', 'NS']:
                        if temp_content.strip()[-1:] != '.':
                            temp_content += '.'

                    if new_record['ttl'] is None:
                        new_record['ttl'] = item['ttl']
                    new_record['records'].append({
                        "content": temp_content,
                        "disabled": temp_disabled
                    })
                final_records.append(new_record)

            else:

                final_records.append({
                        "name": key[0],
                        "type": key[1],
                        "changetype": key[2],
                        "records": [
                            {
                                "content": item['records'][0]['content'],
                                "disabled": item['records'][0]['disabled'],
                                "name": key[0],
                                "ttl": item['records'][0]['ttl'],
                                "type": key[1],
                                "priority": 10,
                            } for item in group
                        ]
                })

        postdata_for_new = {"rrsets": final_records}
        logging.debug(postdata_for_new)
        logging.debug(postdata_for_delete)
        logging.info(
            urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL + '/servers/localhost/zones/{0}'.format(domain)))
        try:
            headers = {}
            headers['X-API-Key'] = self.PDNS_API_KEY
            jdata1 = utils.fetch_json(urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL + '/servers/localhost/zones/{0}'.format(
                domain)), headers=headers, method='PATCH', data=postdata_for_delete)
            jdata2 = utils.fetch_json(
                urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL + '/servers/localhost/zones/{0}'.format(domain)), headers=headers, method='PATCH', data=postdata_for_new)

            if 'error' in jdata1.keys():
                logging.error('Cannot apply record changes.')
                logging.debug(jdata1['error'])
                return {'status': 'error', 'msg': jdata1['error']}
            elif 'error' in jdata2.keys():
                logging.error('Cannot apply record changes.')
                logging.debug(jdata2['error'])
                return {'status': 'error', 'msg': jdata2['error']}
            else:
                self.auto_ptr(domain, new_records, deleted_records)
                self.update_db_serial(domain)
                logging.info('Record was applied successfully.')
                return {'status': 'ok', 'msg': 'Record was applied successfully'}
        except Exception as e:
            logging.error("Cannot apply record changes to domain {0}. Error: {1}".format(domain, e))
            logging.debug(traceback.format_exc())
            return {'status': 'error', 'msg': 'There was something wrong, please contact administrator'}

    def auto_ptr(self, domain, new_records, deleted_records):
        """
        Add auto-ptr records
        """
        domain_obj = Domain.query.filter(Domain.name == domain).first()
        domain_auto_ptr = DomainSetting.query.filter(
            DomainSetting.domain == domain_obj).filter(DomainSetting.setting == 'auto_ptr').first()
        domain_auto_ptr = strtobool(domain_auto_ptr.value) if domain_auto_ptr else False

        system_auto_ptr = Setting().get('auto_ptr')

        if system_auto_ptr or domain_auto_ptr:
            try:
                d = Domain()
                for r in new_records:
                    if r['type'] in ['A', 'AAAA']:
                        r_name = r['name'] + '.'
                        r_content = r['content']
                        reverse_host_address = dns.reversename.from_address(r_content).to_text()
                        domain_reverse_name = d.get_reverse_domain_name(reverse_host_address)
                        d.create_reverse_domain(domain, domain_reverse_name)
                        self.name = dns.reversename.from_address(r_content).to_text().rstrip('.')
                        self.type = 'PTR'
                        self.status = r['disabled']
                        self.ttl = r['ttl']
                        self.data = r_name
                        self.add(domain_reverse_name)
                for r in deleted_records:
                    if r['type'] in ['A', 'AAAA']:
                        r_content = r['content']
                        reverse_host_address = dns.reversename.from_address(r_content).to_text()
                        domain_reverse_name = d.get_reverse_domain_name(reverse_host_address)
                        self.name = reverse_host_address
                        self.type = 'PTR'
                        self.data = r_content
                        self.delete(domain_reverse_name)
                return {'status': 'ok', 'msg': 'Auto-PTR record was updated successfully'}
            except Exception as e:
                logging.error(
                    "Cannot update auto-ptr record changes to domain {0}. DETAIL: {1}".format(domain, e))
                return {'status': 'error', 'msg': 'Auto-PTR creation failed. There was something wrong, please contact administrator.'}

    def delete(self, domain):
        """
        Delete a record from domain
        """
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY
        data = {"rrsets": [
                    {
                        "name": self.name.rstrip('.') + '.',
                        "type": self.type,
                        "changetype": "DELETE",
                        "records": [
                        ]
                    }
                ]
                }
        try:
            jdata = utils.fetch_json(
                urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL + '/servers/localhost/zones/{0}'.format(domain)), headers=headers, method='PATCH', data=data)
            logging.debug(jdata)
            return {'status': 'ok', 'msg': 'Record was removed successfully'}
        except Exception as e:
            logging.error("Cannot remove record {0}/{1}/{2} from domain {3}. DETAIL: {4}".format(
                self.name, self.type, self.data, domain, e))
            return {'status': 'error', 'msg': 'There was something wrong, please contact administrator'}

    def is_allowed_edit(self):
        """
        Check if record is allowed to edit
        """
        return self.type in Setting().get_records_allow_to_edit()

    def is_allowed_delete(self):
        """
        Check if record is allowed to removed
        """
        return (self.type in Setting().get_records_allow_to_edit() and self.type != 'SOA')

    def exists(self, domain):
        """
        Check if record is present within domain records, and if it's present set self to found record
        """
        jdata = self.get_record_data(domain)
        jrecords = jdata['records']

        for jr in jrecords:
            if jr['name'] == self.name and jr['type'] == self.type:
                self.name = jr['name']
                self.type = jr['type']
                self.status = jr['disabled']
                self.ttl = jr['ttl']
                self.data = jr['content']
                self.priority = 10
                return True
        return False

    def update(self, domain, content):
        """
        Update single record
        """
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY

        if self.NEW_SCHEMA:
            data = {"rrsets": [
                        {
                            "name": self.name + '.',
                            "type": self.type,
                            "ttl": self.ttl,
                            "changetype": "REPLACE",
                            "records": [
                                {
                                    "content": content,
                                    "disabled": self.status,
                                }
                            ]
                        }
                    ]
                    }
        else:
            data = {"rrsets": [
                        {
                            "name": self.name,
                            "type": self.type,
                            "changetype": "REPLACE",
                            "records": [
                                {
                                    "content": content,
                                    "disabled": self.status,
                                    "name": self.name,
                                    "ttl": self.ttl,
                                    "type": self.type,
                                    "priority": 10
                                }
                            ]
                        }
                    ]
                    }
        try:
            utils.fetch_json(urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                             '/servers/localhost/zones/{0}'.format(domain)), headers=headers, method='PATCH', data=data)
            logging.debug("dyndns data: {0}".format(data))
            return {'status': 'ok', 'msg': 'Record was updated successfully'}
        except Exception as e:
            logging.error("Cannot add record {0}/{1}/{2} to domain {3}. DETAIL: {4}".format(
                self.name, self.type, self.data, domain, e))
            return {'status': 'error', 'msg': 'There was something wrong, please contact administrator'}

    def update_db_serial(self, domain):
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY
        jdata = utils.fetch_json(
            urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL + '/servers/localhost/zones/{0}'.format(domain)), headers=headers, method='GET')
        serial = jdata['serial']

        domain = Domain.query.filter(Domain.name == domain).first()
        if domain:
            domain.serial = serial
            db.session.commit()
            return {'status': True, 'msg': 'Synced local serial for domain name {0}'.format(domain)}
        else:
            return {'status': False, 'msg': 'Could not find domain name {0} in local db'.format(domain)}


class Server(object):

    """
    This is not a model, it's just an object
    which be assigned data from PowerDNS API
    """

    def __init__(self, server_id=None, server_config=None):
        self.server_id = server_id
        self.server_config = server_config
        # PDNS configs
        self.PDNS_STATS_URL = Setting().get('pdns_api_url')
        self.PDNS_API_KEY = Setting().get('pdns_api_key')
        self.PDNS_VERSION = Setting().get('pdns_version')
        self.API_EXTENDED_URL = utils.pdns_api_extended_uri(self.PDNS_VERSION)

    def get_config(self):
        """
        Get server config
        """
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY

        try:
            jdata = utils.fetch_json(
                urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL + '/servers/{0}/config'.format(self.server_id)), headers=headers, method='GET')
            return jdata
        except Exception as e:
            logging.error("Can not get server configuration. DETAIL: {0}".format(e))
            logging.debug(traceback.format_exc())
            return []

    def get_statistic(self):
        """
        Get server statistics
        """
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY

        try:
            jdata = utils.fetch_json(
                urljoin(self.PDNS_STATS_URL, self.API_EXTENDED_URL + '/servers/{0}/statistics'.format(self.server_id)), headers=headers, method='GET')
            return jdata
        except Exception as e:
            logging.error("Can not get server statistics. DETAIL: {0}".format(e))
            logging.debug(traceback.format_exc())
            return []


class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    msg = db.Column(db.String(256))
    # detail = db.Column(db.Text().with_variant(db.Text(length=2**24-2), 'mysql'))
    detail = db.Column(db.Text())
    created_by = db.Column(db.String(128))
    created_on = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, id=None, msg=None, detail=None, created_by=None):
        self.id = id
        self.msg = msg
        self.detail = detail
        self.created_by = created_by

    def __repr__(self):
        return '<History {0}>'.format(self.msg)

    def add(self):
        """
        Add an event to history table
        """
        h = History()
        h.msg = self.msg
        h.detail = self.detail
        h.created_by = self.created_by
        db.session.add(h)
        db.session.commit()

    def remove_all(self):
        """
        Remove all history from DB
        """
        try:
            db.session.query(History).delete()
            db.session.commit()
            logging.info("Removed all history")
            return True
        except Exception as e:
            db.session.rollback()
            logging.error("Cannot remove history. DETAIL: {0}".format(e))
            logging.debug(traceback.format_exc())
            return False


class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    value = db.Column(db.Text())

    defaults = {
        'maintenance': False,
        'fullscreen_layout': True,
        'record_helper': True,
        'login_ldap_first': True,
        'default_record_table_size': 15,
        'default_domain_table_size': 10,
        'auto_ptr': False,
        'record_quick_edit': True,
        'pretty_ipv6_ptr': False,
        'dnssec_admins_only': False,
        'allow_user_create_domain': False,
        'bg_domain_updates': False,
        'site_name': 'PowerDNS-Admin',
        'session_timeout': 10,
        'pdns_api_url': '',
        'pdns_api_key': '',
        'pdns_version': '4.1.1',
        'local_db_enabled': True,
        'signup_enabled': True,
        'ldap_enabled': False,
        'ldap_type': 'ldap',
        'ldap_uri': '',
        'ldap_base_dn': '',
        'ldap_admin_username': '',
        'ldap_admin_password': '',
        'ldap_filter_basic': '',
        'ldap_filter_username': '',
        'ldap_sg_enabled': False,
        'ldap_admin_group': '',
        'ldap_operator_group': '',
        'ldap_user_group': '',
        'ldap_domain': '',
        'github_oauth_enabled': False,
        'github_oauth_key': '',
        'github_oauth_secret': '',
        'github_oauth_scope': 'email',
        'github_oauth_api_url': 'https://api.github.com/user',
        'github_oauth_token_url': 'https://github.com/login/oauth/access_token',
        'github_oauth_authorize_url': 'https://github.com/login/oauth/authorize',
        'google_oauth_enabled': False,
        'google_oauth_client_id': '',
        'google_oauth_client_secret': '',
        'google_token_url': 'https://oauth2.googleapis.com/token',
        'google_oauth_scope': 'openid email profile',
        'google_authorize_url': 'https://accounts.google.com/o/oauth2/v2/auth',
        'google_base_url': 'https://www.googleapis.com/oauth2/v3/',
        'oidc_oauth_enabled': False,
        'oidc_oauth_key': '',
        'oidc_oauth_secret': '',
        'oidc_oauth_scope': 'email',
        'oidc_oauth_api_url': '',
        'oidc_oauth_token_url': '',
        'oidc_oauth_authorize_url': '',
        'forward_records_allow_edit': {'A': True, 'AAAA': True, 'AFSDB': False, 'ALIAS': False, 'CAA': True, 'CERT': False, 'CDNSKEY': False, 'CDS': False, 'CNAME': True, 'DNSKEY': False, 'DNAME': False, 'DS': False, 'HINFO': False, 'KEY': False, 'LOC': True, 'MX': True, 'NAPTR': False, 'NS': True, 'NSEC': False, 'NSEC3': False, 'NSEC3PARAM': False, 'OPENPGPKEY': False, 'PTR': True, 'RP': False, 'RRSIG': False, 'SOA': False, 'SPF': True, 'SSHFP': False, 'SRV': True, 'TKEY': False, 'TSIG': False, 'TLSA': False, 'SMIMEA': False, 'TXT': True, 'URI': False},
        'reverse_records_allow_edit': {'A': False, 'AAAA': False, 'AFSDB': False, 'ALIAS': False, 'CAA': False, 'CERT': False, 'CDNSKEY': False, 'CDS': False, 'CNAME': False, 'DNSKEY': False, 'DNAME': False, 'DS': False, 'HINFO': False, 'KEY': False, 'LOC': True, 'MX': False, 'NAPTR': False, 'NS': True, 'NSEC': False, 'NSEC3': False, 'NSEC3PARAM': False, 'OPENPGPKEY': False, 'PTR': True, 'RP': False, 'RRSIG': False, 'SOA': False, 'SPF': False, 'SSHFP': False, 'SRV': False, 'TKEY': False, 'TSIG': False, 'TLSA': False, 'SMIMEA': False, 'TXT': True, 'URI': False},
        'ttl_options': '1 minute,5 minutes,30 minutes,60 minutes,24 hours',
    }

    def __init__(self, id=None, name=None, value=None):
        self.id = id
        self.name = name
        self.value = value

    # allow database autoincrement to do its own ID assignments
    def __init__(self, name=None, value=None):
        self.id = None
        self.name = name
        self.value = value

    def set_maintenance(self, mode):
        maintenance = Setting.query.filter(Setting.name == 'maintenance').first()

        if maintenance is None:
            value = self.defaults['maintenance']
            maintenance = Setting(name='maintenance', value=str(value))
            db.session.add(maintenance)

        mode = str(mode)

        try:
            if maintenance.value != mode:
                maintenance.value = mode
                db.session.commit()
            return True
        except Exception as e:
            logging.error('Cannot set maintenance to {0}. DETAIL: {1}'.format(mode, e))
            logging.debug(traceback.format_exec())
            db.session.rollback()
            return False

    def toggle(self, setting):
        current_setting = Setting.query.filter(Setting.name == setting).first()

        if current_setting is None:
            value = self.defaults[setting]
            current_setting = Setting(name=setting, value=str(value))
            db.session.add(current_setting)

        try:
            if current_setting.value == "True":
                current_setting.value = "False"
            else:
                current_setting.value = "True"
            db.session.commit()
            return True
        except Exception as e:
            logging.error('Cannot toggle setting {0}. DETAIL: {1}'.format(setting, e))
            logging.debug(traceback.format_exec())
            db.session.rollback()
            return False

    def set(self, setting, value):
        current_setting = Setting.query.filter(Setting.name == setting).first()

        if current_setting is None:
            current_setting = Setting(name=setting, value=None)
            db.session.add(current_setting)

        value = str(value)

        try:
            current_setting.value = value
            db.session.commit()
            return True
        except Exception as e:
            logging.error('Cannot edit setting {0}. DETAIL: {1}'.format(setting, e))
            logging.debug(traceback.format_exec())
            db.session.rollback()
            return False

    def get(self, setting):
        if setting in self.defaults:
            result = self.query.filter(Setting.name == setting).first()
            if result is not None:
                return strtobool(result.value) if result.value in ['True', 'False'] else result.value
            else:
                return self.defaults[setting]
        else:
            logging.error('Unknown setting queried: {0}'.format(setting))

    def get_records_allow_to_edit(self):
        return list(set(self.get_forward_records_allow_to_edit() + self.get_reverse_records_allow_to_edit()))

    def get_forward_records_allow_to_edit(self):
        records = self.get('forward_records_allow_edit')
        f_records = literal_eval(records) if isinstance(records, str) else records
        r_name = [r for r in f_records if f_records[r]]
        # Sort alphabetically if python version is smaller than 3.6
        if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 6):
            r_name.sort()
        return r_name

    def get_reverse_records_allow_to_edit(self):
        records = self.get('reverse_records_allow_edit')
        r_records = literal_eval(records) if isinstance(records, str) else records
        r_name = [r for r in r_records if r_records[r]]
        # Sort alphabetically if python version is smaller than 3.6
        if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 6):
            r_name.sort()
        return r_name

    def get_ttl_options(self):
        return [(pytimeparse.parse(ttl), ttl) for ttl in self.get('ttl_options').split(',')]


class DomainTemplate(db.Model):
    __tablename__ = "domain_template"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True, unique=True)
    description = db.Column(db.String(255))
    records = db.relationship(
        'DomainTemplateRecord', back_populates='template', cascade="all, delete-orphan")

    def __repr__(self):
        return '<DomainTemplate {0}>'.format(self.name)

    def __init__(self, name=None, description=None):
        self.id = None
        self.name = name
        self.description = description

    def replace_records(self, records):
        try:
            self.records = []
            for record in records:
                self.records.append(record)
            db.session.commit()
            return {'status': 'ok', 'msg': 'Template records have been modified'}
        except Exception as e:
            logging.error('Cannot create template records Error: {0}'.format(e))
            db.session.rollback()
            return {'status': 'error', 'msg': 'Can not create template records'}

    def create(self):
        try:
            db.session.add(self)
            db.session.commit()
            return {'status': 'ok', 'msg': 'Template has been created'}
        except Exception as e:
            logging.error('Can not update domain template table. Error: {0}'.format(e))
            db.session.rollback()
            return {'status': 'error', 'msg': 'Can not update domain template table'}

    def delete_template(self):
        try:
            self.records = []
            db.session.delete(self)
            db.session.commit()
            return {'status': 'ok', 'msg': 'Template has been deleted'}
        except Exception as e:
            logging.error('Can not delete domain template. Error: {0}'.format(e))
            db.session.rollback()
            return {'status': 'error', 'msg': 'Can not delete domain template'}


class DomainTemplateRecord(db.Model):
    __tablename__ = "domain_template_record"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    type = db.Column(db.String(64))
    ttl = db.Column(db.Integer)
    data = db.Column(db.Text)
    status = db.Column(db.Boolean)
    template_id = db.Column(db.Integer, db.ForeignKey('domain_template.id'))
    template = db.relationship('DomainTemplate', back_populates='records')

    def __repr__(self):
        return '<DomainTemplateRecord {0}>'.format(self.id)

    def __init__(self, id=None, name=None, type=None, ttl=None, data=None, status=None):
        self.id = id
        self.name = name
        self.type = type
        self.ttl = ttl
        self.data = data
        self.status = status

    def apply(self):
        try:
            db.session.commit()
        except Exception as e:
            logging.error('Can not update domain template table. Error: {0}'.format(e))
            db.session.rollback()
            return {'status': 'error', 'msg': 'Can not update domain template table'}


class ApiKey(db.Model):
    __tablename__ = "apikey"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.String(255))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', back_populates="apikeys", lazy=True)
    domains = db.relationship(
        "Domain",
        secondary=domain_apikey,
        back_populates="apikeys"
    )

    def __init__(self, key=None, desc=None, role_name=None, domains=[]):
        self.id = None
        self.description = desc
        self.role_name = role_name
        self.domains[:] = domains
        if not key:
            rand_key = ''.join(
                            random.choice(
                                string.ascii_letters + string.digits
                            ) for _ in range(15)
                        )
            self.plain_key = rand_key
            self.key = self.get_hashed_password(rand_key).decode('utf-8')
            logging.debug("Hashed key: {0}".format(self.key))
        else:
            self.key = key

    def create(self):
        try:
            self.role = Role.query.filter(Role.name == self.role_name).first()
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            logging.error('Can not update api key table. Error: {0}'.format(e))
            db.session.rollback()
            raise e

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            msg_str = 'Can not delete api key template. Error: {0}'
            logging.error(msg_str.format(e))
            db.session.rollback()
            raise e

    def update(self, role_name=None, description=None, domains=None):
        try:
            if role_name:
                role = Role.query.filter(Role.name == role_name).first()
                self.role_id = role.id

            if description:
                self.description = description

            if domains:
                domain_object_list = Domain.query \
                                           .filter(Domain.name.in_(domains)) \
                                           .all()
                self.domains[:] = domain_object_list

            db.session.commit()
        except Exception as e:
            msg_str = 'Update of apikey failed. Error: {0}'
            logging.error(msg_str.format(e))
            db.session.rollback
            raise e

    def get_hashed_password(self, plain_text_password=None):
        # Hash a password for the first time
        #   (Using bcrypt, the salt is saved into the hash itself)
        if plain_text_password is None:
            return plain_text_password

        if plain_text_password:
            pw = plain_text_password
        else:
            pw = self.plain_text_password

        return bcrypt.hashpw(
                                pw.encode('utf-8'),
                                app.config.get('SALT').encode('utf-8')
                            )

    def check_password(self, hashed_password):
        # Check hased password. Using bcrypt,
        # the salt is saved into the hash itself
        if (self.plain_text_password):
            return bcrypt.checkpw(
                self.plain_text_password.encode('utf-8'),
                hashed_password.encode('utf-8'))
        return False

    def is_validate(self, method, src_ip=''):
        """
        Validate user credential
        """
        if method == 'LOCAL':
            logging.debug(self.plain_text_password)
            logging.debug(self.get_hashed_password(self.plain_text_password))
            passw_hash = self.get_hashed_password(self.plain_text_password)
            apikey = ApiKey.query \
                           .filter(ApiKey.key == passw_hash.decode('utf-8')) \
                           .first()

            if not apikey:
                raise Exception("Unauthorized")

            return apikey
