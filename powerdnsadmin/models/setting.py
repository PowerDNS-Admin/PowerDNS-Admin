import sys
import traceback

import pytimeparse
from ast import literal_eval
from distutils.util import strtobool
from flask import current_app

from .base import db


class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    value = db.Column(db.Text())
    
    types = {
        'maintenance': bool,
        'fullscreen_layout': bool,
        'record_helper': bool,
        'login_ldap_first': bool,
        'default_record_table_size': int,
        'default_domain_table_size': int,
        'auto_ptr': bool,
        'record_quick_edit': bool,
        'pretty_ipv6_ptr': bool,
        'dnssec_admins_only': bool,
        'allow_user_create_domain': bool,
        'allow_user_remove_domain': bool,
        'allow_user_view_history': bool,
        'custom_history_header': str,
        'delete_sso_accounts': bool,
        'bg_domain_updates': bool,
        'enable_api_rr_history': bool,
        'preserve_history': bool,
        'site_name': str,
        'site_url': str,
        'session_timeout': int,
        'warn_session_timeout': bool,
        'pdns_api_url': str,
        'pdns_api_key': str,
        'pdns_api_timeout': int,
        'pdns_version': str,
        'verify_ssl_connections': bool,
        'verify_user_email': bool,
        'enforce_api_ttl': bool,
        'ttl_options': str,
        'otp_field_enabled': bool,
        'custom_css': str,
        'otp_force': bool,
        'max_history_records': int,
        'deny_domain_override': bool,
        'account_name_extra_chars': bool,
        'gravatar_enabled': bool,
        'forward_records_allow_edit': dict,
        'reverse_records_allow_edit': dict,
        'local_db_enabled': bool,
        'signup_enabled': bool,
        'pwd_enforce_characters': bool,
        'pwd_min_len': int,
        'pwd_min_lowercase': int,
        'pwd_min_uppercase': int,
        'pwd_min_digits': int,
        'pwd_min_special': int,
        'pwd_enforce_complexity': bool,
        'pwd_min_complexity': int,
        'ldap_enabled': bool,
        'ldap_type': str,
        'ldap_uri': str,
        'ldap_base_dn': str,
        'ldap_admin_username': str,
        'ldap_admin_password': str,
        'ldap_domain': str,
        'ldap_filter_basic': str,
        'ldap_filter_username': str,
        'ldap_filter_group': str,
        'ldap_filter_groupname': str,
        'ldap_sg_enabled': bool,
        'ldap_admin_group': str,
        'ldap_operator_group': str,
        'ldap_user_group': str,
        'autoprovisioning': bool,
        'autoprovisioning_attribute': str,
        'urn_value': str,
        'purge': bool,
        'google_oauth_enabled': bool,
        'google_oauth_client_id': str,
        'google_oauth_client_secret': str,
        'google_oauth_scope': str,
        'google_base_url': str,
        'google_oauth_auto_configure': bool,
        'google_oauth_metadata_url': str,
        'google_token_url': str,
        'google_authorize_url': str,
        'github_oauth_enabled': bool,
        'github_oauth_key': str,
        'github_oauth_secret': str,
        'github_oauth_scope': str,
        'github_oauth_api_url': str,
        'github_oauth_auto_configure': bool,
        'github_oauth_metadata_url': str,
        'github_oauth_token_url': str,
        'github_oauth_authorize_url': str,
        'azure_oauth_enabled': bool,
        'azure_oauth_key': str,
        'azure_oauth_secret': str,
        'azure_oauth_scope': str,
        'azure_oauth_api_url': str,
        'azure_oauth_auto_configure': bool,
        'azure_oauth_metadata_url': str,
        'azure_oauth_token_url': str,
        'azure_oauth_authorize_url': str,
        'azure_sg_enabled': bool,
        'azure_admin_group': str,
        'azure_operator_group': str,
        'azure_user_group': str,
        'azure_group_accounts_enabled': bool,
        'azure_group_accounts_name': str,
        'azure_group_accounts_name_re': str,
        'azure_group_accounts_description': str,
        'azure_group_accounts_description_re': str,
        'oidc_oauth_enabled': bool,
        'oidc_oauth_key': str,
        'oidc_oauth_secret': str,
        'oidc_oauth_scope': str,
        'oidc_oauth_api_url': str,
        'oidc_oauth_auto_configure': bool,
        'oidc_oauth_metadata_url': str,
        'oidc_oauth_token_url': str,
        'oidc_oauth_authorize_url': str,
        'oidc_oauth_logout_url': str,
        'oidc_oauth_username': str,
        'oidc_oauth_email': str,
        'oidc_oauth_firstname': str,
        'oidc_oauth_last_name': str,
        'oidc_oauth_account_name_property': str,
        'oidc_oauth_account_description_property': str,
    }
    
    defaults = {
        # General Settings
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
        'allow_user_remove_domain': False,
        'allow_user_view_history': False,
        'custom_history_header': '',
        'delete_sso_accounts': False,
        'bg_domain_updates': False,
        'enable_api_rr_history': True,
        'preserve_history': False,
        'site_name': 'PowerDNS-Admin',
        'site_url': 'http://localhost:9191',
        'session_timeout': 10,
        'warn_session_timeout': True,
        'pdns_api_url': '',
        'pdns_api_key': '',
        'pdns_api_timeout': 30,
        'pdns_version': '4.1.1',
        'verify_ssl_connections': True,
        'verify_user_email': False,
        'enforce_api_ttl': False,
        'ttl_options': '1 minute,5 minutes,30 minutes,60 minutes,24 hours',
        'otp_field_enabled': True,
        'custom_css': '',
        'otp_force': False,
        'max_history_records': 1000,
        'deny_domain_override': False,
        'account_name_extra_chars': False,
        'gravatar_enabled': False,

        # Local Authentication Settings
        'local_db_enabled': True,
        'signup_enabled': True,
        'pwd_enforce_characters': False,
        'pwd_min_len': 10,
        'pwd_min_lowercase': 3,
        'pwd_min_uppercase': 2,
        'pwd_min_digits': 2,
        'pwd_min_special': 1,
        'pwd_enforce_complexity': False,
        'pwd_min_complexity': 11,

        # LDAP Authentication Settings
        'ldap_enabled': False,
        'ldap_type': 'ldap',
        'ldap_uri': '',
        'ldap_base_dn': '',
        'ldap_admin_username': '',
        'ldap_admin_password': '',
        'ldap_domain': '',
        'ldap_filter_basic': '',
        'ldap_filter_username': '',
        'ldap_filter_group': '',
        'ldap_filter_groupname': '',
        'ldap_sg_enabled': False,
        'ldap_admin_group': '',
        'ldap_operator_group': '',
        'ldap_user_group': '',
        'autoprovisioning': False,
        'autoprovisioning_attribute': '',
        'urn_value': '',
        'purge': False,

        # Google OAuth2 Settings
        'google_oauth_enabled': False,
        'google_oauth_client_id': '',
        'google_oauth_client_secret': '',
        'google_oauth_scope': 'openid email profile',
        'google_base_url': 'https://www.googleapis.com/oauth2/v3/',
        'google_oauth_auto_configure': True,
        'google_oauth_metadata_url': 'https://accounts.google.com/.well-known/openid-configuration',
        'google_token_url': 'https://oauth2.googleapis.com/token',
        'google_authorize_url': 'https://accounts.google.com/o/oauth2/v2/auth',

        # GitHub OAuth2 Settings
        'github_oauth_enabled': False,
        'github_oauth_key': '',
        'github_oauth_secret': '',
        'github_oauth_scope': 'email',
        'github_oauth_api_url': 'https://api.github.com/user',
        'github_oauth_auto_configure': False,
        'github_oauth_metadata_url': '',
        'github_oauth_token_url': 'https://github.com/login/oauth/access_token',
        'github_oauth_authorize_url': 'https://github.com/login/oauth/authorize',

        # Azure OAuth2 Settings
        'azure_oauth_enabled': False,
        'azure_oauth_key': '',
        'azure_oauth_secret': '',
        'azure_oauth_scope': 'User.Read openid email profile',
        'azure_oauth_api_url': 'https://graph.microsoft.com/v1.0/',
        'azure_oauth_auto_configure': True,
        'azure_oauth_metadata_url': '',
        'azure_oauth_token_url': '',
        'azure_oauth_authorize_url': '',
        'azure_sg_enabled': False,
        'azure_admin_group': '',
        'azure_operator_group': '',
        'azure_user_group': '',
        'azure_group_accounts_enabled': False,
        'azure_group_accounts_name': 'displayName',
        'azure_group_accounts_name_re': '',
        'azure_group_accounts_description': 'description',
        'azure_group_accounts_description_re': '',

        # OIDC OAuth2 Settings
        'oidc_oauth_enabled': False,
        'oidc_oauth_key': '',
        'oidc_oauth_secret': '',
        'oidc_oauth_scope': 'email',
        'oidc_oauth_api_url': '',
        'oidc_oauth_auto_configure': True,
        'oidc_oauth_metadata_url': '',
        'oidc_oauth_token_url': '',
        'oidc_oauth_authorize_url': '',
        'oidc_oauth_logout_url': '',
        'oidc_oauth_username': 'preferred_username',
        'oidc_oauth_email': 'email',
        'oidc_oauth_firstname': 'given_name',
        'oidc_oauth_last_name': 'family_name',
        'oidc_oauth_account_name_property': '',
        'oidc_oauth_account_description_property': '',

        # Zone Record Settings
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
    }

    groups = {
        'authentication': [
            # Local Authentication Settings
            'local_db_enabled',
            'signup_enabled',
            'pwd_enforce_characters',
            'pwd_min_len',
            'pwd_min_lowercase',
            'pwd_min_uppercase',
            'pwd_min_digits',
            'pwd_min_special',
            'pwd_enforce_complexity',
            'pwd_min_complexity',

            # LDAP Authentication Settings
            'ldap_enabled',
            'ldap_type',
            'ldap_uri',
            'ldap_base_dn',
            'ldap_admin_username',
            'ldap_admin_password',
            'ldap_domain',
            'ldap_filter_basic',
            'ldap_filter_username',
            'ldap_filter_group',
            'ldap_filter_groupname',
            'ldap_sg_enabled',
            'ldap_admin_group',
            'ldap_operator_group',
            'ldap_user_group',
            'autoprovisioning',
            'autoprovisioning_attribute',
            'urn_value',
            'purge',

            # Google OAuth2 Settings
            'google_oauth_enabled',
            'google_oauth_client_id',
            'google_oauth_client_secret',
            'google_oauth_scope',
            'google_base_url',
            'google_oauth_auto_configure',
            'google_oauth_metadata_url',
            'google_token_url',
            'google_authorize_url',

            # GitHub OAuth2 Settings
            'github_oauth_enabled',
            'github_oauth_key',
            'github_oauth_secret',
            'github_oauth_scope',
            'github_oauth_api_url',
            'github_oauth_auto_configure',
            'github_oauth_metadata_url',
            'github_oauth_token_url',
            'github_oauth_authorize_url',

            # Azure OAuth2 Settings
            'azure_oauth_enabled',
            'azure_oauth_key',
            'azure_oauth_secret',
            'azure_oauth_scope',
            'azure_oauth_api_url',
            'azure_oauth_auto_configure',
            'azure_oauth_metadata_url',
            'azure_oauth_token_url',
            'azure_oauth_authorize_url',
            'azure_sg_enabled',
            'azure_admin_group',
            'azure_operator_group',
            'azure_user_group',
            'azure_group_accounts_enabled',
            'azure_group_accounts_name',
            'azure_group_accounts_name_re',
            'azure_group_accounts_description',
            'azure_group_accounts_description_re',

            # OIDC OAuth2 Settings
            'oidc_oauth_enabled',
            'oidc_oauth_key',
            'oidc_oauth_secret',
            'oidc_oauth_scope',
            'oidc_oauth_api_url',
            'oidc_oauth_auto_configure',
            'oidc_oauth_metadata_url',
            'oidc_oauth_token_url',
            'oidc_oauth_authorize_url',
            'oidc_oauth_logout_url',
            'oidc_oauth_username',
            'oidc_oauth_email',
            'oidc_oauth_firstname',
            'oidc_oauth_last_name',
            'oidc_oauth_account_name_property',
            'oidc_oauth_account_description_property',
        ]
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

    def convert_type(self, name, value):
        import json
        from json import JSONDecodeError
        if name in self.types:
            var_type = self.types[name]

            # Handle boolean values
            if var_type == bool:
                if value == 'True' or value == 'true' or value == '1' or value is True:
                    return True
                else:
                    return False

            # Handle float values
            if var_type == float:
                return float(value)

            # Handle integer values
            if var_type == int:
                return int(value)

            if (var_type == dict or var_type == list) and isinstance(value, str) and len(value) > 0:
                try:
                    return json.loads(value)
                except JSONDecodeError as e:
                    pass

            if var_type == str:
                return str(value)

        return value

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

        value = str(self.convert_type(setting, value))

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

            if setting.upper() in current_app.config:
                result = current_app.config[setting.upper()]
            else:
                result = self.query.filter(Setting.name == setting).first()

            if result is not None:
                if hasattr(result, 'value'):
                    result = result.value

                return self.convert_type(setting, result)
            else:
                return self.defaults[setting]
        else:
            current_app.logger.error('Unknown setting queried: {0}'.format(setting))

    def get_group(self, group):
        if not isinstance(group, list):
            group = self.groups[group]

        result = {}
        records = self.query.all()

        for record in records:
            if record.name in group:
                result[record.name] = self.convert_type(record.name, record.value)

        return result

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
