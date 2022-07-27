import os
import base64
import traceback
import bcrypt
import pyotp
import ldap
import ldap.filter
from collections import OrderedDict
from flask import current_app
from flask_login import AnonymousUserMixin
from sqlalchemy import orm
import qrcode as qrc
import qrcode.image.svg as qrc_svg
from io import BytesIO

from .base import db
from .role import Role
from .setting import Setting
from .domain_user import DomainUser
from .account_user import AccountUser


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
    accounts = None

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
        return str(self.id)

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
        # Check hashed password. Using bcrypt, the salt is saved into the hash itself
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

    def ldap_search(self, searchFilter, baseDN, retrieveAttributes=None):
        searchScope = ldap.SCOPE_SUBTREE

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

    def is_validate(self, method, src_ip='', trust_user=False):
        """
        Validate user credential
        """
        role_name = 'User'

        if method == 'LOCAL':
            user_info = User.query.filter(
                User.username == self.username).first()

            if user_info:
                if trust_user or (user_info.password and self.check_password(
                        user_info.password)):
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
            if Setting().get('ldap_type') == 'ad' and not trust_user:
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

                    if Setting().get('ldap_type') != 'ad' and not trust_user:
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
                                ldap_group_security_roles = OrderedDict(
                                    Administrator=LDAP_ADMIN_GROUP,
                                    Operator=LDAP_OPERATOR_GROUP,
                                    User=LDAP_USER_GROUP,
                                )
                                user_dn = ldap_result[0][0][0]
                                sf_groups = ""

                                for group in ldap_group_security_roles.values():
                                    if not group:
                                        continue

                                    sf_groups += f"(distinguishedName={group})"

                                sf_member_user = f"(member:1.2.840.113556.1.4.1941:={user_dn})"
                                search_filter = f"(&(|{sf_groups}){sf_member_user})"
                                current_app.logger.debug(f"LDAP groupSearchFilter '{search_filter}'")

                                ldap_user_groups = [
                                    group[0][0]
                                    for group in self.ldap_search(
                                        search_filter,
                                        LDAP_BASE_DN
                                    )
                                ]

                                if not ldap_user_groups:
                                    current_app.logger.error(
                                        f"User '{self.username}' "
                                        "does not belong to any group "
                                        "while LDAP_GROUP_SECURITY_ENABLED is ON"
                                    )
                                    return False

                                current_app.logger.debug(
                                    "LDAP User security groups "
                                    f"for user '{self.username}': "
                                    " ".join(ldap_user_groups)
                                )

                                for role, ldap_group in ldap_group_security_roles.items():
                                    # Continue when groups is not defined or
                                    # user is'nt member of LDAP group
                                    if not ldap_group or not ldap_group in ldap_user_groups:
                                        continue

                                    role_name = role
                                    current_app.logger.info(
                                        f"User '{self.username}' member of "
                                        f"the '{ldap_group}' group that allows "
                                        f"'{role}' access to to PowerDNS-Admin"
                                    )

                                    # Stop loop on first found
                                    break

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
        if self.role_id is None:
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
        if self.plain_text_password:
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

    def get_user_domains(self):
        from ..models.base import db
        from .account import Account
        from .domain import Domain
        from .account_user import AccountUser
        from .domain_user import DomainUser

        domains = db.session.query(Domain) \
        .outerjoin(DomainUser, Domain.id == DomainUser.domain_id) \
        .outerjoin(Account, Domain.account_id == Account.id) \
        .outerjoin(AccountUser, Account.id == AccountUser.account_id) \
        .filter(
                db.or_(
                DomainUser.user_id == self.id,
                AccountUser.user_id == self.id
                )).all()
        return domains

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

    def revoke_privilege(self, update_user=False):
        """
        Revoke all privileges from a user
        """
        user = User.query.filter(User.username == self.username).first()

        if user:
            user_id = user.id
            try:
                DomainUser.query.filter(DomainUser.user_id == user_id).delete()
                if (update_user)==True:
                    AccountUser.query.filter(AccountUser.user_id == user_id).delete()
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

    @orm.reconstructor
    def set_account(self):
        self.accounts = self.get_accounts()

    def get_accounts(self):
        """
        Get accounts associated with this user
        """
        from .account import Account
        from .account_user import AccountUser
        accounts = []
        query = db.session\
            .query(
                AccountUser,
                Account)\
            .filter(self.id == AccountUser.user_id)\
            .filter(Account.id == AccountUser.account_id)\
            .order_by(Account.name)\
            .all()
        for q in query:
            accounts.append(q[1])
        return accounts

    def get_qrcode_value(self):
        img = qrc.make(self.get_totp_uri(),
                    image_factory=qrc_svg.SvgPathImage)
        stream = BytesIO()
        img.save(stream)
        return stream.getvalue()


    def read_entitlements(self, key):
        """
        Get entitlements from ldap server associated with this user
        """
        LDAP_BASE_DN = Setting().get('ldap_base_dn')
        LDAP_FILTER_USERNAME = Setting().get('ldap_filter_username')
        LDAP_FILTER_BASIC = Setting().get('ldap_filter_basic')
        searchFilter = "(&({0}={1}){2})".format(LDAP_FILTER_USERNAME,
                                                        self.username,
                                                        LDAP_FILTER_BASIC)
        current_app.logger.debug('Ldap searchFilter {0}'.format(searchFilter))
        ldap_result = self.ldap_search(searchFilter, LDAP_BASE_DN, [key])
        current_app.logger.debug('Ldap search result: {0}'.format(ldap_result))
        entitlements=[]
        if ldap_result:
            dict=ldap_result[0][0][1]
            if len(dict)!=0:
                for entitlement in dict[key]:
                    entitlements.append(entitlement.decode("utf-8"))
            else:
                e="Not found value in the autoprovisioning attribute field "
                current_app.logger.warning("Cannot apply autoprovisioning on user: {}".format(e))
        return entitlements

    def updateUser(self, Entitlements):
        """
        Update user associations based on ldap attribute
        """
        entitlements= getCorrectEntitlements(Entitlements)
        if len(entitlements)!=0:
            self.revoke_privilege(True)
            for entitlement in entitlements:
                arguments=entitlement.split(':')
                entArgs=arguments[arguments.index('powerdns-admin')+1:]
                role= entArgs[0]
                self.set_role(role)
                if (role=="User") and len(entArgs)>1:
                    current_domains=getUserInfo(self.get_user_domains())
                    current_accounts=getUserInfo(self.get_accounts())
                    domain=entArgs[1]
                    self.addMissingDomain(domain, current_domains)
                    if len(entArgs)>2:
                        account=entArgs[2]
                        self.addMissingAccount(account, current_accounts)

    def addMissingDomain(self, autoprovision_domain, current_domains):
        """
        Add domain gathered by autoprovisioning to the current domains list of a user
        """
        from ..models.domain import Domain
        user = db.session.query(User).filter(User.username == self.username).first()
        if autoprovision_domain not in current_domains:
            domain= db.session.query(Domain).filter(Domain.name == autoprovision_domain).first()
            if domain!=None:
                domain.add_user(user)

    def addMissingAccount(self, autoprovision_account, current_accounts):
        """
        Add account gathered by autoprovisioning to the current accounts list of a user
        """
        from ..models.account import Account
        user = db.session.query(User).filter(User.username == self.username).first()
        if autoprovision_account not in current_accounts:
            account= db.session.query(Account).filter(Account.name == autoprovision_account).first()
            if account!=None:
                account.add_user(user)

def getCorrectEntitlements(Entitlements):
    """
    Gather a list of valid records from the ldap attribute given
    """
    from ..models.role import Role
    urn_value=Setting().get('urn_value')
    urnArgs=[x.lower() for x in urn_value.split(':')]
    entitlements=[]
    for Entitlement in Entitlements:
        arguments=Entitlement.split(':')

        if ('powerdns-admin' in arguments):
            prefix=arguments[0:arguments.index('powerdns-admin')]
            prefix=[x.lower() for x in prefix]
            if (prefix!=urnArgs):
                e= "Typo in first part of urn value"
                current_app.logger.warning("Cannot apply autoprovisioning on user: {}".format(e))
                continue

        else:
            e="Entry not a PowerDNS-Admin record"
            current_app.logger.warning("Cannot apply autoprovisioning on user: {}".format(e))
            continue

        if len(arguments)<=len(urnArgs)+1: #prefix:powerdns-admin
            e="No value given after the prefix"
            current_app.logger.warning("Cannot apply autoprovisioning on user: {}".format(e))
            continue

        entArgs=arguments[arguments.index('powerdns-admin')+1:]
        role=entArgs[0]
        roles= Role.query.all()
        role_names=get_role_names(roles)

        if role not in role_names:
            e="Role given by entry not a role availabe in PowerDNS-Admin. Check for spelling errors"
            current_app.logger.warning("Cannot apply autoprovisioning on user: {}".format(e))
            continue

        if len(entArgs)>1:
            if (role!="User"):
                e="Too many arguments for Admin or Operator"
                current_app.logger.warning("Cannot apply autoprovisioning on user: {}".format(e))
                continue
            else:
                if len(entArgs)<=3:
                    if entArgs[1] and not checkIfDomainExists(entArgs[1]):
                        continue
                    if len(entArgs)==3:
                        if entArgs[2] and not checkIfAccountExists(entArgs[2]):
                            continue
                else:
                    e="Too many arguments"
                    current_app.logger.warning("Cannot apply autoprovisioning on user: {}".format(e))
                    continue

        entitlements.append(Entitlement)

    return entitlements


def checkIfDomainExists(domainName):
    from ..models.domain import Domain
    domain= db.session.query(Domain).filter(Domain.name == domainName)
    if len(domain.all())==0:
        e= domainName + " is not found in the database"
        current_app.logger.warning("Cannot apply autoprovisioning on user: {}".format(e))
        return False
    return True

def checkIfAccountExists(accountName):
    from ..models.account import Account
    account= db.session.query(Account).filter(Account.name == accountName)
    if len(account.all())==0:
        e= accountName + " is not found in the database"
        current_app.logger.warning("Cannot apply autoprovisioning on user: {}".format(e))
        return False
    return True

def get_role_names(roles):
    """
    returns all the roles available in database in string format
    """
    roles_list=[]
    for role in roles:
        roles_list.append(role.name)
    return roles_list

def getUserInfo(DomainsOrAccounts):
    current=[]
    for DomainOrAccount in DomainsOrAccounts:
        current.append(DomainOrAccount.name)
    return current
