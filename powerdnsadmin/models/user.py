import os
import base64
import bcrypt
import traceback
import pyotp
import ldap
import ldap.filter
from flask import current_app
from flask_login import AnonymousUserMixin

from .base import db
from .role import Role
from .setting import Setting
from .domain_user import DomainUser


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
    otp_secret = db.Column(db.String(16))
    confirmed = db.Column(db.SmallInteger, nullable=False, default=0)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    def __init__(self,
                 id=None,
                 username=None,
                 password=None,
                 plain_text_password=None,
                 firstname=None,
                 lastname=None,
                 role_id=None,
                 email=None,
                 otp_secret=None,
                 confirmed=False,
                 reload_info=True):
        self.id = id
        self.username = username
        self.password = password
        self.plain_text_password = plain_text_password
        self.firstname = firstname
        self.lastname = lastname
        self.role_id = role_id
        self.email = email
        self.otp_secret = otp_secret
        self.confirmed = confirmed

        if reload_info:
            user_info = self.get_user_info_by_id(
            ) if id else self.get_user_info_by_username()

            if user_info:
                self.id = user_info.id
                self.username = user_info.username
                self.firstname = user_info.firstname
                self.lastname = user_info.lastname
                self.email = user_info.email
                self.role_id = user_info.role_id
                self.otp_secret = user_info.otp_secret
                self.confirmed = user_info.confirmed

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
        return "otpauth://totp/PowerDNS-Admin:{0}?secret={1}&issuer=PowerDNS-Admin".format(
            self.username, self.otp_secret)

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
            return bcrypt.checkpw(self.plain_text_password.encode('utf-8'),
                                  hashed_password.encode('utf-8'))
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
                    "{0}@{1}".format(self.username,
                                     Setting().get('ldap_domain')),
                    self.password)
            else:
                conn.simple_bind_s(Setting().get('ldap_admin_username'),
                                   Setting().get('ldap_admin_password'))
            ldap_result_id = conn.search(baseDN, searchScope, searchFilter,
                                         retrieveAttributes)
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
            current_app.logger.error(e)
            current_app.logger.debug('baseDN: {0}'.format(baseDN))
            current_app.logger.debug(traceback.format_exc())

    def ldap_auth(self, ldap_username, password):
        try:
            conn = self.ldap_init_conn()
            conn.simple_bind_s(ldap_username, password)
            return True
        except ldap.LDAPError as e:
            current_app.logger.error(e)
            return False

    def ad_recursive_groups(self, groupDN):
        """
        Recursively list groups belonging to a group. It will allow checking deep in the Active Directory
        whether a user is allowed to enter or not
        """
        LDAP_BASE_DN = Setting().get('ldap_base_dn')
        groupSearchFilter = "(&(objectcategory=group)(member=%s))" % ldap.filter.escape_filter_chars(
            groupDN)
        result = [groupDN]
        try:
            groups = self.ldap_search(groupSearchFilter, LDAP_BASE_DN)
            for group in groups:
                result += [group[0][0]]
                if 'memberOf' in group[0][1]:
                    for member in group[0][1]['memberOf']:
                        result += self.ad_recursive_groups(
                            member.decode("utf-8"))
            return result
        except ldap.LDAPError as e:
            current_app.logger.exception("Recursive AD Group search error")
            return result

    def is_validate(self, method, src_ip=''):
        """
        Validate user credential
        """
        role_name = 'User'

        if method == 'LOCAL':
            user_info = User.query.filter(
                User.username == self.username).first()

            if user_info:
                if user_info.password and self.check_password(
                        user_info.password):
                    current_app.logger.info(
                        'User "{0}" logged in successfully. Authentication request from {1}'
                        .format(self.username, src_ip))
                    return True
                current_app.logger.error(
                    'User "{0}" inputted a wrong password. Authentication request from {1}'
                    .format(self.username, src_ip))
                return False

            current_app.logger.warning(
                'User "{0}" does not exist. Authentication request from {1}'.
                format(self.username, src_ip))
            return False

        if method == 'LDAP':
            LDAP_TYPE = Setting().get('ldap_type')
            LDAP_BASE_DN = Setting().get('ldap_base_dn')
            LDAP_FILTER_BASIC = Setting().get('ldap_filter_basic')
            LDAP_FILTER_USERNAME = Setting().get('ldap_filter_username')
            LDAP_FILTER_GROUP = Setting().get('ldap_filter_group')
            LDAP_FILTER_GROUPNAME = Setting().get('ldap_filter_groupname')
            LDAP_ADMIN_GROUP = Setting().get('ldap_admin_group')
            LDAP_OPERATOR_GROUP = Setting().get('ldap_operator_group')
            LDAP_USER_GROUP = Setting().get('ldap_user_group')
            LDAP_GROUP_SECURITY_ENABLED = Setting().get('ldap_sg_enabled')

            # validate AD user password
            if Setting().get('ldap_type') == 'ad':
                ldap_username = "{0}@{1}".format(self.username,
                                                 Setting().get('ldap_domain'))
                if not self.ldap_auth(ldap_username, self.password):
                    current_app.logger.error(
                        'User "{0}" input a wrong LDAP password. Authentication request from {1}'
                        .format(self.username, src_ip))
                    return False

            searchFilter = "(&({0}={1}){2})".format(LDAP_FILTER_USERNAME,
                                                    self.username,
                                                    LDAP_FILTER_BASIC)
            current_app.logger.debug('Ldap searchFilter {0}'.format(searchFilter))

            ldap_result = self.ldap_search(searchFilter, LDAP_BASE_DN)
            current_app.logger.debug('Ldap search result: {0}'.format(ldap_result))

            if not ldap_result:
                current_app.logger.warning(
                    'LDAP User "{0}" does not exist. Authentication request from {1}'
                    .format(self.username, src_ip))
                return False
            else:
                try:
                    ldap_username = ldap.filter.escape_filter_chars(
                        ldap_result[0][0][0])

                    if Setting().get('ldap_type') != 'ad':
                        # validate ldap user password
                        if not self.ldap_auth(ldap_username, self.password):
                            current_app.logger.error(
                                'User "{0}" input a wrong LDAP password. Authentication request from {1}'
                                .format(self.username, src_ip))
                            return False

                    # check if LDAP_GROUP_SECURITY_ENABLED is True
                    # user can be assigned to ADMIN or USER role.
                    if LDAP_GROUP_SECURITY_ENABLED:
                        try:
                            if LDAP_TYPE == 'ldap':
                                groupSearchFilter = "(&({0}={1}){2})".format(LDAP_FILTER_GROUPNAME, ldap_username, LDAP_FILTER_GROUP)
                                current_app.logger.debug('Ldap groupSearchFilter {0}'.format(groupSearchFilter))
                                if (self.ldap_search(groupSearchFilter,
                                                     LDAP_ADMIN_GROUP)):
                                    role_name = 'Administrator'
                                    current_app.logger.info(
                                        'User {0} is part of the "{1}" group that allows admin access to PowerDNS-Admin'
                                        .format(self.username,
                                                LDAP_ADMIN_GROUP))
                                elif (self.ldap_search(groupSearchFilter,
                                                       LDAP_OPERATOR_GROUP)):
                                    role_name = 'Operator'
                                    current_app.logger.info(
                                        'User {0} is part of the "{1}" group that allows operator access to PowerDNS-Admin'
                                        .format(self.username,
                                                LDAP_OPERATOR_GROUP))
                                elif (self.ldap_search(groupSearchFilter,
                                                       LDAP_USER_GROUP)):
                                    current_app.logger.info(
                                        'User {0} is part of the "{1}" group that allows user access to PowerDNS-Admin'
                                        .format(self.username,
                                                LDAP_USER_GROUP))
                                else:
                                    current_app.logger.error(
                                        'User {0} is not part of the "{1}", "{2}" or "{3}" groups that allow access to PowerDNS-Admin'
                                        .format(self.username,
                                                LDAP_ADMIN_GROUP,
                                                LDAP_OPERATOR_GROUP,
                                                LDAP_USER_GROUP))
                                    return False
                            elif LDAP_TYPE == 'ad':
                                user_ldap_groups = []
                                user_ad_member_of = ldap_result[0][0][1].get(
                                    'memberOf')

                                if not user_ad_member_of:
                                    current_app.logger.error(
                                        'User {0} does not belong to any group while LDAP_GROUP_SECURITY_ENABLED is ON'
                                        .format(self.username))
                                    return False

                                for group in [
                                        g.decode("utf-8")
                                        for g in user_ad_member_of
                                ]:
                                    user_ldap_groups += self.ad_recursive_groups(
                                        group)

                                if (LDAP_ADMIN_GROUP in user_ldap_groups):
                                    role_name = 'Administrator'
                                    current_app.logger.info(
                                        'User {0} is part of the "{1}" group that allows admin access to PowerDNS-Admin'
                                        .format(self.username,
                                                LDAP_ADMIN_GROUP))
                                elif (LDAP_OPERATOR_GROUP in user_ldap_groups):
                                    role_name = 'Operator'
                                    current_app.logger.info(
                                        'User {0} is part of the "{1}" group that allows operator access to PowerDNS-Admin'
                                        .format(self.username,
                                                LDAP_OPERATOR_GROUP))
                                elif (LDAP_USER_GROUP in user_ldap_groups):
                                    current_app.logger.info(
                                        'User {0} is part of the "{1}" group that allows user access to PowerDNS-Admin'
                                        .format(self.username,
                                                LDAP_USER_GROUP))
                                else:
                                    current_app.logger.error(
                                        'User {0} is not part of the "{1}", "{2}" or "{3}" groups that allow access to PowerDNS-Admin'
                                        .format(self.username,
                                                LDAP_ADMIN_GROUP,
                                                LDAP_OPERATOR_GROUP,
                                                LDAP_USER_GROUP))
                                    return False
                            else:
                                current_app.logger.error('Invalid LDAP type')
                                return False
                        except Exception as e:
                            current_app.logger.error(
                                'LDAP group lookup for user "{0}" has failed. Authentication request from {1}'
                                .format(self.username, src_ip))
                            current_app.logger.debug(traceback.format_exc())
                            return False

                except Exception as e:
                    current_app.logger.error('Wrong LDAP configuration. {0}'.format(e))
                    current_app.logger.debug(traceback.format_exc())
                    return False

            # create user if not exist in the db
            if not User.query.filter(User.username == self.username).first():
                self.firstname = self.username
                self.lastname = ''
                try:
                    # try to get user's firstname, lastname and email address from LDAP attributes
                    if LDAP_TYPE == 'ldap':
                        self.firstname = ldap_result[0][0][1]['givenName'][
                            0].decode("utf-8")
                        self.lastname = ldap_result[0][0][1]['sn'][0].decode(
                            "utf-8")
                        self.email = ldap_result[0][0][1]['mail'][0].decode(
                            "utf-8")
                    elif LDAP_TYPE == 'ad':
                        self.firstname = ldap_result[0][0][1]['name'][
                            0].decode("utf-8")
                        self.email = ldap_result[0][0][1]['userPrincipalName'][
                            0].decode("utf-8")
                except Exception as e:
                    current_app.logger.warning(
                        "Reading ldap data threw an exception {0}".format(e))
                    current_app.logger.debug(traceback.format_exc())

                # first register user will be in Administrator role
                if User.query.count() == 0:
                    self.role_id = Role.query.filter_by(
                        name='Administrator').first().id
                else:
                    self.role_id = Role.query.filter_by(
                        name=role_name).first().id

                self.create_user()
                current_app.logger.info('Created user "{0}" in the DB'.format(
                    self.username))

            # user already exists in database, set their role based on group membership (if enabled)
            if LDAP_GROUP_SECURITY_ENABLED:
                self.set_role(role_name)

            return True
        else:
            current_app.logger.error('Unsupported authentication method')
            return False

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
            self.role_id = Role.query.filter_by(
                name='Administrator').first().id

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
                return {
                    'status': False,
                    'msg': 'New email address is already in use'
                }

        user.firstname = self.firstname
        user.lastname = self.lastname
        user.email = self.email

        # store new password hash (only if changed)
        if self.plain_text_password != "":
            user.password = self.get_hashed_password(
                self.plain_text_password).decode("utf-8")

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
        user.password = self.get_hashed_password(
            self.plain_text_password).decode(
                "utf-8") if self.plain_text_password else user.password

        if self.email:
            # Can not update to a new email that
            # already been used.
            existing_email = User.query.filter(
                User.email == self.email,
                User.username != self.username).first()
            if existing_email:
                return False
            # If need to verify new email,
            # update the "confirmed" status.
            if user.email != self.email:
                user.email = self.email
                if Setting().get('verify_user_email'):
                    user.confirmed = 0

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

    def update_confirmed(self, confirmed):
        """
        Update user email confirmation status
        """
        self.confirmed = confirmed
        db.session.commit()

    def get_domains(self):
        """
        Get list of domains which the user is granted to have
        access.

        Note: This doesn't include the permission granting from Account
        which user belong to
        """

        return self.get_domain_query().all()

    def delete(self):
        """
        Delete a user
        """
        # revoke all user privileges first
        self.revoke_privilege()

        try:
            User.query.filter(User.username == self.username).delete()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error('Cannot delete user {0} from DB. DETAIL: {1}'.format(
                self.username, e))
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
                current_app.logger.error(
                    'Cannot revoke user {0} privileges. DETAIL: {1}'.format(
                        self.username, e))
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