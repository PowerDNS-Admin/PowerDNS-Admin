import os
from pathlib import Path

basedir = os.path.abspath(Path(os.path.dirname(__file__)).parent)

class AppSettings(object):

    defaults = {
        # Flask Settings
        'bind_address': '0.0.0.0',
        'csrf_cookie_secure': False,
        'log_level': 'WARNING',
        'port': 9191,
        'salt': '$2b$12$yLUMTIfl21FKJQpTkRQXCu',
        'secret_key': 'e951e5a1f4b94151b360f47edf596dd2',
        'session_cookie_secure': False,
        'session_type': 'sqlalchemy',
        'sqlalchemy_track_modifications': True,
        'sqlalchemy_database_uri': 'sqlite:///' + os.path.join(basedir, 'pdns.db'),
        'sqlalchemy_engine_options': {},

        # General Settings
        'captcha_enable': True,
        'captcha_height': 60,
        'captcha_length': 6,
        'captcha_session_key': 'captcha_image',
        'captcha_width': 160,
        'mail_server': 'localhost',
        'mail_port': 25,
        'mail_debug': False,
        'mail_use_ssl': False,
        'mail_use_tls': False,
        'mail_username': '',
        'mail_password': '',
        'mail_default_sender': '',
        'remote_user_enabled': False,
        'remote_user_cookies': [],
        'remote_user_logout_url': '',
        'hsts_enabled': False,
        'server_external_ssl': True,
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
        'pdns_admin_log_level': 'WARNING',

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

        # Google OAuth Settings
        'google_oauth_enabled': False,
        'google_oauth_client_id': '',
        'google_oauth_client_secret': '',
        'google_oauth_scope': 'openid email profile',
        'google_base_url': 'https://www.googleapis.com/oauth2/v3/',
        'google_oauth_auto_configure': True,
        'google_oauth_metadata_url': 'https://accounts.google.com/.well-known/openid-configuration',
        'google_token_url': 'https://oauth2.googleapis.com/token',
        'google_authorize_url': 'https://accounts.google.com/o/oauth2/v2/auth',

        # GitHub OAuth Settings
        'github_oauth_enabled': False,
        'github_oauth_key': '',
        'github_oauth_secret': '',
        'github_oauth_scope': 'email',
        'github_oauth_api_url': 'https://api.github.com/user',
        'github_oauth_auto_configure': False,
        'github_oauth_metadata_url': '',
        'github_oauth_token_url': 'https://github.com/login/oauth/access_token',
        'github_oauth_authorize_url': 'https://github.com/login/oauth/authorize',

        # Azure OAuth Settings
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

        # OIDC OAuth Settings
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

        # SAML Authentication Settings
        'saml_enabled': False,
        'saml_debug': False,
        'saml_path': os.path.join(basedir, 'saml'),
        'saml_metadata_url': None,
        'saml_metadata_cache_lifetime': 1,
        'saml_idp_sso_binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
        'saml_idp_entity_id': None,
        'saml_nameid_format': None,
        'saml_attribute_account': None,
        'saml_attribute_email': 'email',
        'saml_attribute_givenname': 'givenname',
        'saml_attribute_surname': 'surname',
        'saml_attribute_name': None,
        'saml_attribute_username': None,
        'saml_attribute_admin': None,
        'saml_attribute_group': None,
        'saml_group_admin_name': None,
        'saml_group_operator_name': None,
        'saml_group_to_account_mapping': None,
        'saml_sp_entity_id': None,
        'saml_sp_contact_name': None,
        'saml_sp_contact_mail': None,
        'saml_sign_request': False,
        'saml_want_message_signed': True,
        'saml_logout': True,
        'saml_logout_url': None,
        'saml_assertion_encrypted': True,
        'saml_cert': None,
        'saml_key': None,

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

    types = {
        # Flask Settings
        'bind_address': str,
        'csrf_cookie_secure': bool,
        'log_level': str,
        'port': int,
        'salt': str,
        'secret_key': str,
        'session_cookie_secure': bool,
        'session_type': str,
        'sqlalchemy_track_modifications': bool,
        'sqlalchemy_database_uri': str,
        'sqlalchemy_engine_options': dict,

        # General Settings
        'captcha_enable': bool,
        'captcha_height': int,
        'captcha_length': int,
        'captcha_session_key': str,
        'captcha_width': int,
        'mail_server': str,
        'mail_port': int,
        'mail_debug': bool,
        'mail_use_ssl': bool,
        'mail_use_tls': bool,
        'mail_username': str,
        'mail_password': str,
        'mail_default_sender': str,
        'hsts_enabled': bool,
        'remote_user_enabled': bool,
        'remote_user_cookies': list,
        'remote_user_logout_url': str,
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
        'pdns_admin_log_level': str,
        'forward_records_allow_edit': dict,
        'reverse_records_allow_edit': dict,

        # Local Authentication Settings
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

        # LDAP Authentication Settings
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

        # Google OAuth Settings
        'google_oauth_enabled': bool,
        'google_oauth_client_id': str,
        'google_oauth_client_secret': str,
        'google_oauth_scope': str,
        'google_base_url': str,
        'google_oauth_auto_configure': bool,
        'google_oauth_metadata_url': str,
        'google_token_url': str,
        'google_authorize_url': str,

        # GitHub OAuth Settings
        'github_oauth_enabled': bool,
        'github_oauth_key': str,
        'github_oauth_secret': str,
        'github_oauth_scope': str,
        'github_oauth_api_url': str,
        'github_oauth_auto_configure': bool,
        'github_oauth_metadata_url': str,
        'github_oauth_token_url': str,
        'github_oauth_authorize_url': str,

        # Azure OAuth Settings
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

        # OIDC OAuth Settings
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

        # SAML Authentication Settings
        'saml_enabled': bool,
        'saml_debug': bool,
        'saml_path': str,
        'saml_metadata_url': str,
        'saml_metadata_cache_lifetime': int,
        'saml_idp_sso_binding': str,
        'saml_idp_entity_id': str,
        'saml_nameid_format': str,
        'saml_attribute_account': str,
        'saml_attribute_email': str,
        'saml_attribute_givenname': str,
        'saml_attribute_surname': str,
        'saml_attribute_name': str,
        'saml_attribute_username': str,
        'saml_attribute_admin': str,
        'saml_attribute_group': str,
        'saml_group_admin_name': str,
        'saml_group_operator_name': str,
        'saml_group_to_account_mapping': str,
        'saml_sp_entity_id': str,
        'saml_sp_contact_name': str,
        'saml_sp_contact_mail': str,
        'saml_sign_request': bool,
        'saml_want_message_signed': bool,
        'saml_logout': bool,
        'saml_logout_url': str,
        'saml_assertion_encrypted': bool,
        'saml_cert': str,
        'saml_key': str,
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

            # Google OAuth Settings
            'google_oauth_enabled',
            'google_oauth_client_id',
            'google_oauth_client_secret',
            'google_oauth_scope',
            'google_base_url',
            'google_oauth_auto_configure',
            'google_oauth_metadata_url',
            'google_token_url',
            'google_authorize_url',

            # GitHub OAuth Settings
            'github_oauth_enabled',
            'github_oauth_key',
            'github_oauth_secret',
            'github_oauth_scope',
            'github_oauth_api_url',
            'github_oauth_auto_configure',
            'github_oauth_metadata_url',
            'github_oauth_token_url',
            'github_oauth_authorize_url',

            # Azure OAuth Settings
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

            # OIDC OAuth Settings
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

    @staticmethod
    def convert_type(name, value):
        import json
        from json import JSONDecodeError
        if name in AppSettings.types:
            var_type = AppSettings.types[name]

            # Handle boolean values
            if var_type == bool and isinstance(value, str):
                if value.lower() in ['True', 'true', '1'] or value is True:
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
                    # Provide backwards compatibility for legacy non-JSON format
                    value = value.replace("'", '"').replace('True', 'true').replace('False', 'false')
                    try:
                        return json.loads(value)
                    except JSONDecodeError as e:
                        raise ValueError('Cannot parse json {} for variable {}'.format(value, name))

            if var_type == str:
                return str(value)

        return value

    @staticmethod
    def load_environment(app):
        """ Load app settings from environment variables when defined. """
        import os

        for var_name, default_value in AppSettings.defaults.items():
            env_name = var_name.upper()
            current_value = None

            if env_name + '_FILE' in os.environ:
                if env_name in os.environ:
                    raise AttributeError(
                        "Both {} and {} are set but are exclusive.".format(
                            env_name, env_name + '_FILE'))
                with open(os.environ[env_name + '_FILE']) as f:
                    current_value = f.read()
                f.close()

            elif env_name in os.environ:
                current_value = os.environ[env_name]

            if current_value is not None:
                app.config[env_name] = AppSettings.convert_type(var_name, current_value)
