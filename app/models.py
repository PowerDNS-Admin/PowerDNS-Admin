import os
import ldap3
import time
import base64
import bcrypt
import itertools
import traceback
import pyotp

from datetime import datetime
from distutils.version import StrictVersion
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

from flask_login import AnonymousUserMixin

from app import app, db
from app.lib import utils
from app.lib.log import logger
logging = logger('MODEL', app.config['LOG_LEVEL'], app.config['LOG_FILE']).config()

if 'LDAP_TYPE' in list(app.config.keys()):
    LDAP_URI = app.config['LDAP_URI']
    LDAP_USERNAME = app.config['LDAP_USERNAME']
    LDAP_PASSWORD = app.config['LDAP_PASSWORD']
    LDAP_SEARCH_BASE = app.config['LDAP_SEARCH_BASE']
    LDAP_TYPE = app.config['LDAP_TYPE']
    LDAP_FILTER = app.config['LDAP_FILTER']
    LDAP_USERNAMEFIELD = app.config['LDAP_USERNAMEFIELD']
else:
    LDAP_TYPE = False
if 'PRETTY_IPV6_PTR' in list(app.config.keys()):
    import dns.inet
    import dns.name
    import dns.reversename
    PRETTY_IPV6_PTR = app.config['PRETTY_IPV6_PTR']
else:
    PRETTY_IPV6_PTR = False

PDNS_STATS_URL = app.config['PDNS_STATS_URL']
PDNS_API_KEY = app.config['PDNS_API_KEY']
PDNS_VERSION = app.config['PDNS_VERSION']
API_EXTENDED_URL = utils.pdns_api_extended_uri(PDNS_VERSION)

# Flag for pdns v4.x.x
# TODO: Find another way to do this
if StrictVersion(PDNS_VERSION) >= StrictVersion('4.0.0'):
    NEW_SCHEMA = True
else:
    NEW_SCHEMA = False

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
        return '<User %r>' % (self.username)

    def get_totp_uri(self):
        return 'otpauth://totp/PowerDNS-Admin:%s?secret=%s&issuer=PowerDNS-Admin' % (self.username, self.otp_secret)

    def verify_totp(self, token):
        totp = pyotp.TOTP(self.otp_secret)
        return totp.verify(int(token))

    def get_hashed_password(self, plain_text_password=None):
        # Hash a password for the first time
        #   (Using bcrypt, the salt is saved into the hash itself)
        pw = plain_text_password if plain_text_password else self.plain_text_password
        return bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())

    def check_password(self, hashed_password):
        # Check hased password. Useing bcrypt, the salt is saved into the hash itself
        return bcrypt.checkpw(self.plain_text_password.encode('utf-8'), hashed_password.encode('utf-8'))

    def get_user_info_by_id(self):
        user_info = User.query.get(int(self.id))
        return user_info

    def get_user_info_by_username(self):
        user_info = User.query.filter(User.username == self.username).first()
        return user_info

    def ldap_search(self, searchFilter, baseDN, attributes=None):
        try:
            server = ldap3.Server(LDAP_URI)
            conn = ldap3.Connection(server, LDAP_USERNAME, LDAP_PASSWORD, auto_bind=True)
            results = conn.search(baseDN, searchFilter, attributes=attributes)
            if results:
                return conn.entries
            return False

        except ldap3.LDAPException as e:
            logging.error(e)
            raise

    def is_validate(self, method):
        """
        Validate user credential
        """
        if method == 'LOCAL':
            user_info = User.query.filter(User.username == self.username).first()

            if user_info:
                if user_info.password and self.check_password(user_info.password):
                    logging.info('User "%s" logged in successfully' % self.username)
                    return True
                logging.error('User "%s" input a wrong password' % self.username)
                return False

            logging.warning('User "%s" does not exist' % self.username)
            return False

        if method == 'LDAP':
            if not LDAP_TYPE:
                logging.error('LDAP authentication is disabled')
                return False

            searchFilter = "(&(objectcategory=person)(samaccountname=%s))" % self.username
            if LDAP_TYPE == 'ldap':
              searchFilter = "(&(%s=%s)%s)" % (LDAP_USERNAMEFIELD, self.username, LDAP_FILTER)
              logging.info('Ldap searchFilter "%s"' % searchFilter)

            attributes = ['dn', 'sn', 'givenName', 'mail']
            result = self.ldap_search(searchFilter, LDAP_SEARCH_BASE, attributes=attributes)
            if not result:
                logging.warning('User "%s" does not exist' % self.username)
                return False

            server = ldap3.Server(LDAP_URI)

            try:
                ldap_username = result[1]._dn
                ldap3.Connection(server, ldap_username, self.password, auto_bind=True)
                logging.info('User "%s" logged in successfully' % self.username)
            except Exception:
                logging.error('User "%s" input a wrong password' % self.username)
                return False

            # create user if not exist in the db
            if not User.query.filter(User.username == self.username).first():
                try:
                    # try to get user's firstname & lastname from LDAP
                    # this might be changed in the future
                    self.firstname = str(result[1].givenName)
                    self.lastname = str(result[1].sn)
                    self.email = str(result[1].mail)
                except Exception:
                    self.firstname = self.username
                    self.lastname = ''

                # first register user will be in Administrator role
                self.role_id = Role.query.filter_by(name='User').first().id
                if User.query.count() == 0:
                    self.role_id = Role.query.filter_by(name='Administrator').first().id

                self.create_user()
                logging.info('Created user "%s" in the DB' % self.username)

            return True

        logging.error('Unsupported authentication method')
        return False

    def create_user(self):
        """
        If user logged in successfully via LDAP in the first time
        We will create a local user (in DB) in order to manage user
        profile such as name, roles,...
        """
        db.session.add(self)
        db.session.commit()

    def create_local_user(self):
        """
        Create local user witch stores username / password in the DB
        """
        # check if username existed
        user = User.query.filter(User.username == self.username).first()
        if user:
            return 'Username already existed'

        # check if email existed
        user = User.query.filter(User.email == self.email).first()
        if user:
            return 'Email already existed'

        # first register user will be in Administrator role
        self.role_id = Role.query.filter_by(name='User').first().id
        if User.query.count() == 0:
            self.role_id = Role.query.filter_by(name='Administrator').first().id
        self.password = self.get_hashed_password(self.plain_text_password)

        db.session.add(self)
        db.session.commit()
        return True

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
        user.password = self.get_hashed_password(self.plain_text_password) if self.plain_text_password else user.password
        user.avatar = self.avatar if self.avatar else user.avatar

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

    def get_domain(self):
        """
        Get domains which user has permission to
        access
        """
        user_domains = []
        query = db.session.query(User, DomainUser, Domain).filter(User.id==self.id).filter(User.id==DomainUser.user_id).filter(Domain.id==DomainUser.domain_id).all()
        for q in query:
            user_domains.append(q[2])
        return user_domains

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
        except:
            db.session.rollback()
            logging.error('Cannot delete user %s from DB' % self.username)
            return False

    def revoke_privilege(self):
        """
        Revoke all privielges from a user
        """
        user = User.query.filter(User.username == self.username).first()

        if user:
            user_id = user.id
            try:
                DomainUser.query.filter(DomainUser.user_id == user_id).delete()
                db.session.commit()
                return True
            except:
                db.session.rollback()
                logging.error('Cannot revoke user %s privielges.' % self.username)
                return False
        return False

    def set_admin(self, is_admin):
        """
        Set role for a user:
            is_admin == True  => Administrator
            is_admin == False => User
        """
        user_role_name = 'Administrator' if is_admin else 'User'
        role = Role.query.filter(Role.name==user_role_name).first()

        try:
            if role:
                user = User.query.filter(User.username==self.username).first()
                user.role_id = role.id
                db.session.commit()
                return True
            else:
                return False
        except:
            db.session.roleback()
            logging.error('Cannot change user role in DB')
            logging.debug(traceback.format_exc())
            return False


class Role(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(64), index=True, unique=True)
    description = db.Column(db.String(128))
    users = db.relationship('User', backref='role', lazy='dynamic')

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
        return '<Role %r>' % (self.name)

class DomainSetting(db.Model):
    __tablename__ = 'domain_setting'
    id = db.Column(db.Integer, primary_key = True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'))
    domain = db.relationship('Domain', back_populates='settings')
    setting = db.Column(db.String(255), nullable = False)
    value = db.Column(db.String(255))

    def __init__(self, id=None, setting=None, value=None):
        self.id = id
        self.setting = setting
        self.value = value

    def __repr__(self):
        return '<DomainSetting %r for $d>' % (setting, self.domain.name)

    def __eq__(self, other):
        return self.setting == other.setting

    def set(self, value):
        try:
            self.value = value
            db.session.commit()
            return True
        except:
            logging.error('Unable to set DomainSetting value')
            logging.debug(traceback.format_exc())
            db.session.rollback()
            return False

class Domain(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(255), index=True, unique=True)
    master = db.Column(db.String(128))
    type = db.Column(db.String(6), nullable = False)
    serial = db.Column(db.Integer)
    notified_serial = db.Column(db.Integer)
    last_check = db.Column(db.Integer)
    dnssec = db.Column(db.Integer)
    settings = db.relationship('DomainSetting', back_populates='domain')

    def __init__(self, id=None, name=None, master=None, type='NATIVE', serial=None, notified_serial=None, last_check=None, dnssec=None):
        self.id = id
        self.name = name
        self.master = master
        self.type = type
        self.serial = serial
        self.notified_serial = notified_serial
        self.last_check = last_check
        self.dnssec = dnssec

    def __repr__(self):
        return '<Domain %r>' % (self.name)

    def add_setting(self, setting, value):
        try:
            self.settings.append(DomainSetting(setting=setting, value=value))
            db.session.commit()
            return True
        except Exception as e:
            logging.error('Can not create settting %s for domain %s. %s' % (setting, self.name, str(e)))
            return False

    def get_domains(self):
        """
        Get all domains which has in PowerDNS
        jdata example:
            [
              {
                "id": "example.org.",
                "url": "/servers/localhost/zones/example.org.",
                "name": "example.org",
                "kind": "Native",
                "dnssec": false,
                "account": "",
                "masters": [],
                "serial": 2015101501,
                "notified_serial": 0,
                "last_check": 0
              }
            ]
        """
        headers = {}
        headers['X-API-Key'] = PDNS_API_KEY
        jdata = utils.fetch_json(urljoin(PDNS_STATS_URL, API_EXTENDED_URL + '/servers/localhost/zones'), headers=headers)
        return jdata

    def get_id_by_name(self, name):
        """
        Return domain id
        """
        domain = Domain.query.filter(Domain.name==name).first()
        return domain.id

    def update(self):
        """
        Fetch zones (domains) from PowerDNS and update into DB
        """
        db_domain = Domain.query.all()
        list_db_domain = [d.name for d in db_domain]
        dict_db_domain = dict((x.name,x) for x in db_domain)

        headers = {}
        headers['X-API-Key'] = PDNS_API_KEY
        try:
            jdata = utils.fetch_json(urljoin(PDNS_STATS_URL, API_EXTENDED_URL + '/servers/localhost/zones'), headers=headers)
            list_jdomain = [d['name'].rstrip('.') for d in jdata]
            try:
                # domains should remove from db since it doesn't exist in powerdns anymore
                should_removed_db_domain = list(set(list_db_domain).difference(list_jdomain))
                for d in should_removed_db_domain:
                    # revoke permission before delete domain
                    domain = Domain.query.filter(Domain.name==d).first()
                    domain_user = DomainUser.query.filter(DomainUser.domain_id==domain.id)
                    if domain_user:
                        domain_user.delete()
                        db.session.commit()

                    # then remove domain
                    Domain.query.filter(Domain.name == d).delete()
                    db.session.commit()
            except:
                logging.error('Can not delete domain from DB')
                logging.debug(traceback.format_exc())
                db.session.rollback()

            # update/add new domain
            for data in jdata:
                d = dict_db_domain.get(data['name'].rstrip('.'), None)
                changed = False
                if d:
                    # existing domain, only update if something actually has changed
                    if ( d.master != str(data['masters'])
                        or d.type != data['kind']
                        or d.serial != data['serial']
                        or d.notified_serial != data['notified_serial']
                        or d.last_check != ( 1 if data['last_check'] else 0 )
                        or d.dnssec != data['dnssec'] ):

                            d.master = str(data['masters'])
                            d.type = data['kind']
                            d.serial = data['serial']
                            d.notified_serial = data['notified_serial']
                            d.last_check = 1 if data['last_check'] else 0
                            d.dnssec = 1 if data['dnssec'] else 0
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
                    db.session.add(d)
                    changed = True
                if changed:
                    try:
                        db.session.commit()
                    except:
                        db.session.rollback()
            return {'status': 'ok', 'msg': 'Domain table has been updated successfully'}
        except Exception as e:
            logging.error('Can not update domain table.' + str(e))
            return {'status': 'error', 'msg': 'Can not update domain table'}

    def add(self, domain_name, domain_type, soa_edit_api, domain_ns=[], domain_master_ips=[]):
        """
        Add a domain to power dns
        """
        headers = {}
        headers['X-API-Key'] = PDNS_API_KEY

        if NEW_SCHEMA:
            domain_name = domain_name + '.'
            domain_ns = [ns + '.' for ns in domain_ns]

        if soa_edit_api == 'OFF':
            post_data = {
                            "name": domain_name,
                            "kind": domain_type,
                            "masters": domain_master_ips,
                            "nameservers": domain_ns,
                        }
        else:
            post_data = {
                                "name": domain_name,
                                "kind": domain_type,
                                "masters": domain_master_ips,
                                "nameservers": domain_ns,
                                "soa_edit_api": soa_edit_api
                            }

        try:
            jdata = utils.fetch_json(urljoin(PDNS_STATS_URL, API_EXTENDED_URL + '/servers/localhost/zones'), headers=headers, method='POST', data=post_data)
            if 'error' in list(jdata.keys()):
                logging.error(jdata['error'])
                return {'status': 'error', 'msg': jdata['error']}
            else:
                logging.info('Added domain %s successfully' % domain_name)
                return {'status': 'ok', 'msg': 'Added domain successfully'}
        except Exception as e:
            traceback.print_exc()
            logging.error('Cannot add domain %s' % domain_name)
            logging.debug(str(e))
            return {'status': 'error', 'msg': 'Cannot add this domain.'}


    def delete(self, domain_name):
        """
        Delete a single domain name from powerdns
        """
        headers = {}
        headers['X-API-Key'] = PDNS_API_KEY
        try:
            jdata = utils.fetch_json(urljoin(PDNS_STATS_URL, API_EXTENDED_URL + '/servers/localhost/zones/%s' % domain_name), headers=headers, method='DELETE')
            logging.info('Delete domain %s successfully' % domain_name)
            return {'status': 'ok', 'msg': 'Delete domain successfully'}
        except Exception as e:
            traceback.print_exc()
            logging.error('Cannot delete domain %s' % domain_name)
            logging.debug(str(e))
            return {'status': 'error', 'msg': 'Cannot delete domain'}

    def get_user(self):
        """
        Get users (id) who have access to this domain name
        """
        user_ids = []
        query = db.session.query(DomainUser, Domain).filter(User.id==DomainUser.user_id).filter(Domain.id==DomainUser.domain_id).filter(Domain.name==self.name).all()
        for q in query:
            user_ids.append(q[0].user_id)
        return user_ids

    def grant_privielges(self, new_user_list):
        """
        Reconfigure domain_user table
        """

        domain_id = self.get_id_by_name(self.name)

        domain_user_ids = self.get_user()
        new_user_ids = [u.id for u in User.query.filter(User.username.in_(new_user_list)).all()] if new_user_list else []

        removed_ids = list(set(domain_user_ids).difference(new_user_ids))
        added_ids = list(set(new_user_ids).difference(domain_user_ids))

        try:
            for uid in removed_ids:
                DomainUser.query.filter(DomainUser.user_id == uid).filter(DomainUser.domain_id==domain_id).delete()
                db.session.commit()
        except:
            db.session.rollback()
            logging.error('Cannot revoke user privielges on domain %s' % self.name)

        try:
            for uid in added_ids:
                du = DomainUser(domain_id, uid)
                db.session.add(du)
                db.session.commit()
        except:
            db.session.rollback()
            logging.error('Cannot grant user privielges to domain %s' % self.name)


    def update_from_master(self, domain_name):
        """
        Update records from Master DNS server
        """
        domain = Domain.query.filter(Domain.name == domain_name).first()
        if domain:
            headers = {}
            headers['X-API-Key'] = PDNS_API_KEY
            try:
                jdata = utils.fetch_json(urljoin(PDNS_STATS_URL, API_EXTENDED_URL + '/servers/localhost/zones/%s/axfr-retrieve' % domain), headers=headers, method='PUT')
                return {'status': 'ok', 'msg': 'Update from Master successfully'}
            except:
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
            headers['X-API-Key'] = PDNS_API_KEY
            try:
                jdata = utils.fetch_json(urljoin(PDNS_STATS_URL, API_EXTENDED_URL + '/servers/localhost/zones/%s/cryptokeys' % domain.name), headers=headers, method='GET')
                if 'error' in jdata:
                    return {'status': 'error', 'msg': 'DNSSEC is not enabled for this domain'}
                else:
                    return {'status': 'ok', 'dnssec': jdata}
            except:
                return {'status': 'error', 'msg': 'There was something wrong, please contact administrator'}
        else:
            return {'status': 'error', 'msg': 'This domain doesnot exist'}


class DomainUser(db.Model):
    __tablename__ = 'domain_user'
    id = db.Column(db.Integer, primary_key = True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'), nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)

    def __init__(self, domain_id, user_id):
        self.domain_id = domain_id
        self.user_id = user_id

    def __repr__(self):
        return '<Domain_User %r %r>' % (self.domain_id, self.user_id)


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

    def get_record_data(self, domain):
        """
        Query domain's DNS records via API
        """
        headers = {}
        headers['X-API-Key'] = PDNS_API_KEY
        try:
            jdata = utils.fetch_json(urljoin(PDNS_STATS_URL, API_EXTENDED_URL + '/servers/localhost/zones/%s' % domain), headers=headers)
        except:
            logging.error("Cannot fetch domain's record data from remote powerdns api")
            return False

        if NEW_SCHEMA:
            rrsets = jdata['rrsets']
            for rrset in rrsets:
                r_name = rrset['name'].rstrip('.')
                if PRETTY_IPV6_PTR: # only if activated
                    if rrset['type'] == 'PTR': # only ptr
                        if 'ip6.arpa' in r_name: # only if v6-ptr
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
        check = [check for check in records if check['name'] == self.name]
        if check:
            r = check[0]
            if r['type'] in ('A', 'AAAA' ,'CNAME'):
                return {'status': 'error', 'msg': 'Record already exists with type "A", "AAAA" or "CNAME"'}

        # continue if the record is ready to be added
        headers = {}
        headers['X-API-Key'] = PDNS_API_KEY

        if NEW_SCHEMA:
            data = {"rrsets": [
                        {
                            "name": self.name + '.',
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
            jdata = utils.fetch_json(urljoin(PDNS_STATS_URL, API_EXTENDED_URL + '/servers/localhost/zones/%s' % domain), headers=headers, method='PATCH', data=data)
            logging.debug(jdata)
            return {'status': 'ok', 'msg': 'Record was added successfully'}
        except Exception as e:
            logging.error("Cannot add record %s/%s/%s to domain %s. DETAIL: %s" % (self.name, self.type, self.data, domain, str(e)))
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
        list_current_records = [[x['name'],x['type']] for x in current_records]
        list_new_records = [[x['name'],x['type']] for x in new_records]

        # get list of deleted records
        # they are the records which exist in list_current_records but not in list_new_records
        list_deleted_records = [x for x in list_current_records if x not in list_new_records]

        # convert back to list of hash
        deleted_records = [x for x in current_records if [x['name'],x['type']] in list_deleted_records and x['type'] in app.config['RECORDS_ALLOW_EDIT']]

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
            if PRETTY_IPV6_PTR: # only if activated
                if NEW_SCHEMA: # only if new schema
                    if r_type == 'PTR': # only ptr
                        if ':' in r['record_name']: # dirty ipv6 check
                            r_name = r['record_name']
            
            record = {
                        "name": r_name,
                        "type": r_type,
                        "content": r['record_data'],
                        "disabled": True if r['record_status'] == 'Disabled' else False,
                        "ttl": int(r['record_ttl']) if r['record_ttl'] else 3600,
                    }
            records.append(record)
        
        deleted_records, new_records = self.compare(domain, records)

        records = []
        for r in deleted_records:
            r_name = r['name'] + '.' if NEW_SCHEMA else r['name']
            r_type = r['type']
            if PRETTY_IPV6_PTR: # only if activated
                if NEW_SCHEMA: # only if new schema
                    if r_type == 'PTR': # only ptr
                        if ':' in r['name']: # dirty ipv6 check
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
            if NEW_SCHEMA:
                r_name = r['name'] + '.'
                r_type = r['type']
                if PRETTY_IPV6_PTR: # only if activated
                    if r_type == 'PTR': # only ptr
                        if ':' in r['name']: # dirty ipv6 check
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
                                    "priority": 10, # priority field for pdns 3.4.1. https://doc.powerdns.com/md/authoritative/upgrading/
                                }
                            ]
                        }

            records.append(record)

        # Adjustment to add multiple records which described in https://github.com/ngoduykhanh/PowerDNS-Admin/issues/5#issuecomment-181637576
        final_records = []
        records = sorted(records, key = lambda item: (item["name"], item["type"], item["changetype"]))
        for key, group in itertools.groupby(records, lambda item: (item["name"], item["type"], item["changetype"])):
            if NEW_SCHEMA:
                r_name = key[0]
                r_type = key[1]
                r_changetype = key[2]
                
                if PRETTY_IPV6_PTR: # only if activated
                    if r_type == 'PTR': # only ptr
                        if ':' in r_name: # dirty ipv6 check
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

        try:
            headers = {}
            headers['X-API-Key'] = PDNS_API_KEY
            jdata1 = utils.fetch_json(urljoin(PDNS_STATS_URL, API_EXTENDED_URL + '/servers/localhost/zones/%s' % domain), headers=headers, method='PATCH', data=postdata_for_delete)
            jdata2 = utils.fetch_json(urljoin(PDNS_STATS_URL, API_EXTENDED_URL + '/servers/localhost/zones/%s' % domain), headers=headers, method='PATCH', data=postdata_for_new)

            if 'error' in list(jdata2.keys()):
                logging.error('Cannot apply record changes.')
                logging.debug(jdata2['error'])
                return {'status': 'error', 'msg': jdata2['error']}
            else:
                logging.info('Record was applied successfully.')
                return {'status': 'ok', 'msg': 'Record was applied successfully'}
        except Exception as e:
            logging.error("Cannot apply record changes to domain %s. DETAIL: %s" % (str(e), domain))
            return {'status': 'error', 'msg': 'There was something wrong, please contact administrator'}


    def delete(self, domain):
        """
        Delete a record from domain
        """
        headers = {}
        headers['X-API-Key'] = PDNS_API_KEY
        data = {"rrsets": [
                    {
                        "name": self.name,
                        "type": self.type,
                        "changetype": "DELETE",
                        "records": [
                            {
                                "name": self.name,
                                "type": self.type
                            }
                        ]
                    }
                ]
            }
        try:
            jdata = utils.fetch_json(urljoin(PDNS_STATS_URL, API_EXTENDED_URL + '/servers/localhost/zones/%s' % domain), headers=headers, method='PATCH', data=data)
            logging.debug(jdata)
            return {'status': 'ok', 'msg': 'Record was removed successfully'}
        except:
            logging.error("Cannot remove record %s/%s/%s from domain %s" % (self.name, self.type, self.data, domain))
            return {'status': 'error', 'msg': 'There was something wrong, please contact administrator'}

    def is_allowed(self):
        """
        Check if record is allowed to edit/removed
        """
        return self.type in app.config['RECORDS_ALLOW_EDIT']

    def exists(self, domain):
        """
        Check if record is present within domain records, and if it's present set self to found record
        """
        jdata = self.get_record_data(domain)
        jrecords = jdata['records']

        for jr in jrecords:
            if jr['name'] == self.name:
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
        headers['X-API-Key'] = PDNS_API_KEY

        if NEW_SCHEMA:
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
            jdata = utils.fetch_json(urljoin(PDNS_STATS_URL, API_EXTENDED_URL + '/servers/localhost/zones/%s' % domain), headers=headers, method='PATCH', data=data)
            logging.debug("dyndns data: " % data)
            return {'status': 'ok', 'msg': 'Record was updated successfully'}
        except Exception as e:
            logging.error("Cannot add record %s/%s/%s to domain %s. DETAIL: %s" % (self.name, self.type, self.data, domain, str(e)))
            return {'status': 'error', 'msg': 'There was something wrong, please contact administrator'}


class Server(object):
    """
    This is not a model, it's just an object
    which be assigned data from PowerDNS API
    """

    def __init__(self, server_id=None, server_config=None):
        self.server_id = server_id
        self.server_config = server_config

    def get_config(self):
        """
        Get server config
        """
        headers = {}
        headers['X-API-Key'] = PDNS_API_KEY

        try:
            jdata = utils.fetch_json(urljoin(PDNS_STATS_URL, API_EXTENDED_URL + '/servers/%s/config' % self.server_id), headers=headers, method='GET')
            return jdata
        except:
            logging.error("Can not get server configuration.")
            logging.debug(traceback.format_exc())
            return []

    def get_statistic(self):
        """
        Get server statistics
        """
        headers = {}
        headers['X-API-Key'] = PDNS_API_KEY

        try:
            jdata = utils.fetch_json(urljoin(PDNS_STATS_URL, API_EXTENDED_URL + '/servers/%s/statistics' % self.server_id), headers=headers, method='GET')
            return jdata
        except:
            logging.error("Can not get server statistics.")
            logging.debug(traceback.format_exc())
            return []


class History(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    msg = db.Column(db.String(256))
    detail = db.Column(db.Text().with_variant(db.Text(length=2**24-2), 'mysql'))
    created_by = db.Column(db.String(128))
    created_on = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, id=None, msg=None, detail=None, created_by=None):
        self.id = id
        self.msg = msg
        self.detail = detail
        self.created_by = created_by

    def __repr__(self):
        return '<History %r>' % (self.msg)

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
            num_rows_deleted = db.session.query(History).delete()
            db.session.commit()
            logging.info("Removed all history")
            return True
        except:
            db.session.rollback()
            logging.error("Cannot remove history")
            logging.debug(traceback.format_exc())
            return False

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(64))
    value = db.Column(db.String(256))

    def __init__(self, id=None, name=None, value=None):
        self.id = id
        self.name = name
        self.value = value

    # allow database autoincrement to do its own ID assignments
    def __init__(self, name=None, value=None):
        self.id = None
        self.name = name
        self.value = value

    def set_mainteance(self, mode):
        """
        mode = True/False
        """
        mode = str(mode)
        maintenance = Setting.query.filter(Setting.name=='maintenance').first()
        try:
            if maintenance:
                if maintenance.value != mode:
                    maintenance.value = mode
                    db.session.commit()
                return True
            else:
                s = Setting(name='maintenance', value=mode)
                db.session.add(s)
                db.session.commit()
                return True
        except:
            logging.error('Cannot set maintenance to %s' % mode)
            logging.debug(traceback.format_exc())
            db.session.rollback()
            return False

    def toggle(self, setting):
        setting = str(setting)
        current_setting = Setting.query.filter(Setting.name==setting).first()
        try:
            if current_setting:
                if current_setting.value == "True":
                    current_setting.value = "False"
                else:
                    current_setting.value = "True"
                db.session.commit()
                return True
            else:
                logging.error('Setting %s does not exist' % setting)
                return False
        except:
            logging.error('Cannot toggle setting %s' % setting)
            logging.debug(traceback.format_exec())
            db.session.rollback()
            return False

    def set(self, setting, value):
        setting = str(setting)
        new_value = str(value)
        current_setting = Setting.query.filter(Setting.name==setting).first()
        try:
            if current_setting:
                current_setting.value = new_value
                db.session.commit()
                return True
            else:
                logging.error('Setting %s does not exist' % setting)
                return False
        except:
            logging.error('Cannot edit setting %s' % setting)
            logging.debug(traceback.format_exec())
            db.session.rollback()
            return False
