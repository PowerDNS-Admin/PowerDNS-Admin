import sys
import pytimeparse
from ast import literal_eval
from distutils.util import strtobool
from flask import current_app

from .base import db


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
        'site_url': 'http://localhost:9191',
        'session_timeout': 10,
        'warn_session_timeout': True,
        'pdns_api_url': '',
        'pdns_api_key': '',
        'pdns_api_timeout': 30,
        'pdns_version': '4.1.1',
        'verify_ssl_connections': True,
        'local_db_enabled': True,
        'signup_enabled': True,
        'verify_user_email': False,
        'ldap_enabled': False,
        'ldap_type': 'ldap',
        'ldap_uri': '',
        'ldap_base_dn': '',
        'ldap_admin_username': '',
        'ldap_admin_password': '',
        'ldap_filter_basic': '',
        'ldap_filter_group': '',
        'ldap_filter_username': '',
        'ldap_filter_groupname': '',
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
        'github_oauth_token_url':
        'https://github.com/login/oauth/access_token',
        'github_oauth_authorize_url':
        'https://github.com/login/oauth/authorize',
        'google_oauth_enabled': False,
        'google_oauth_client_id': '',
        'google_oauth_client_secret': '',
        'google_token_url': 'https://oauth2.googleapis.com/token',
        'google_oauth_scope': 'openid email profile',
        'google_authorize_url': 'https://accounts.google.com/o/oauth2/v2/auth',
        'google_base_url': 'https://www.googleapis.com/oauth2/v3/',
        'azure_oauth_enabled': False,
        'azure_oauth_key': '',
        'azure_oauth_secret': '',
        'azure_oauth_scope': 'User.Read openid email profile',
        'azure_oauth_api_url': 'https://graph.microsoft.com/v1.0/',
        'azure_oauth_token_url':
        'https://login.microsoftonline.com/[tenancy]/oauth2/v2.0/token',
        'azure_oauth_authorize_url':
        'https://login.microsoftonline.com/[tenancy]/oauth2/v2.0/authorize',
        'azure_sg_enabled': False,
        'azure_admin_group': '',
        'azure_operator_group': '',
        'azure_user_group': '',
        'oidc_oauth_enabled': False,
        'oidc_oauth_key': '',
        'oidc_oauth_secret': '',
        'oidc_oauth_scope': 'email',
        'oidc_oauth_api_url': '',
        'oidc_oauth_token_url': '',
        'oidc_oauth_authorize_url': '',
        'forward_records_allow_edit': {
            'A': True,
            'AAAA': True,
            'AFSDB': False,
            'ALIAS': False,
            'CAA': True,
            'CERT': False,
            'CDNSKEY': False,
            'CDS': False,
            'CNAME': True,
            'DNSKEY': False,
            'DNAME': False,
            'DS': False,
            'HINFO': False,
            'KEY': False,
            'LOC': True,
            'LUA': False,
            'MX': True,
            'NAPTR': False,
            'NS': True,
            'NSEC': False,
            'NSEC3': False,
            'NSEC3PARAM': False,
            'OPENPGPKEY': False,
            'PTR': True,
            'RP': False,
            'RRSIG': False,
            'SOA': False,
            'SPF': True,
            'SSHFP': False,
            'SRV': True,
            'TKEY': False,
            'TSIG': False,
            'TLSA': False,
            'SMIMEA': False,
            'TXT': True,
            'URI': False
        },
        'reverse_records_allow_edit': {
            'A': False,
            'AAAA': False,
            'AFSDB': False,
            'ALIAS': False,
            'CAA': False,
            'CERT': False,
            'CDNSKEY': False,
            'CDS': False,
            'CNAME': False,
            'DNSKEY': False,
            'DNAME': False,
            'DS': False,
            'HINFO': False,
            'KEY': False,
            'LOC': True,
            'LUA': False,
            'MX': False,
            'NAPTR': False,
            'NS': True,
            'NSEC': False,
            'NSEC3': False,
            'NSEC3PARAM': False,
            'OPENPGPKEY': False,
            'PTR': True,
            'RP': False,
            'RRSIG': False,
            'SOA': False,
            'SPF': False,
            'SSHFP': False,
            'SRV': False,
            'TKEY': False,
            'TSIG': False,
            'TLSA': False,
            'SMIMEA': False,
            'TXT': True,
            'URI': False
        },
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
        maintenance = Setting.query.filter(
            Setting.name == 'maintenance').first()

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
            current_app.logger.error('Cannot set maintenance to {0}. DETAIL: {1}'.format(
                mode, e))
            current_app.logger.debug(traceback.format_exec())
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
            current_app.logger.error('Cannot toggle setting {0}. DETAIL: {1}'.format(
                setting, e))
            current_app.logger.debug(traceback.format_exec())
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
            current_app.logger.error('Cannot edit setting {0}. DETAIL: {1}'.format(
                setting, e))
            current_app.logger.debug(traceback.format_exec())
            db.session.rollback()
            return False

    def get(self, setting):
        if setting in self.defaults:
            result = self.query.filter(Setting.name == setting).first()
            if result is not None:
                return strtobool(result.value) if result.value in [
                    'True', 'False'
                ] else result.value
            else:
                return self.defaults[setting]
        else:
            current_app.logger.error('Unknown setting queried: {0}'.format(setting))

    def get_records_allow_to_edit(self):
        return list(
            set(self.get_forward_records_allow_to_edit() +
                self.get_reverse_records_allow_to_edit()))

    def get_forward_records_allow_to_edit(self):
        records = self.get('forward_records_allow_edit')
        f_records = literal_eval(records) if isinstance(records,
                                                        str) else records
        r_name = [r for r in f_records if f_records[r]]
        # Sort alphabetically if python version is smaller than 3.6
        if sys.version_info[0] < 3 or (sys.version_info[0] == 3
                                       and sys.version_info[1] < 6):
            r_name.sort()
        return r_name

    def get_reverse_records_allow_to_edit(self):
        records = self.get('reverse_records_allow_edit')
        r_records = literal_eval(records) if isinstance(records,
                                                        str) else records
        r_name = [r for r in r_records if r_records[r]]
        # Sort alphabetically if python version is smaller than 3.6
        if sys.version_info[0] < 3 or (sys.version_info[0] == 3
                                       and sys.version_info[1] < 6):
            r_name.sort()
        return r_name

    def get_ttl_options(self):
        return [(pytimeparse.parse(ttl), ttl)
                for ttl in self.get('ttl_options').split(',')]
