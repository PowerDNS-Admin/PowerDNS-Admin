import os
from pathlib import Path
from .settings import Settings, Setting

basedir = os.path.abspath(Path(os.path.dirname(__file__)).parent)
initialized = False
inst = Settings.instance()


class SettingMap:
    ACCOUNT_NAME_EXTRA_CHARS = 'account_name_extra_chars'
    ALLOW_USER_CREATE_DOMAIN = 'allow_user_create_domain'
    ALLOW_USER_REMOVE_DOMAIN = 'allow_user_remove_domain'
    ALLOW_USER_VIEW_HISTORY = 'allow_user_view_history'
    AUTOPROVISIONING = 'autoprovisioning'
    AUTOPROVISIONING_ATTRIBUTE = 'autoprovisioning_attribute'
    AUTO_PTR = 'auto_ptr'
    AZURE_ADMIN_GROUP = 'azure_admin_group'
    AZURE_GROUP_ACCOUNTS_DESCRIPTION = 'azure_group_accounts_description'
    AZURE_GROUP_ACCOUNTS_DESCRIPTION_RE = 'azure_group_accounts_description_re'
    AZURE_GROUP_ACCOUNTS_ENABLED = 'azure_group_accounts_enabled'
    AZURE_GROUP_ACCOUNTS_NAME = 'azure_group_accounts_name'
    AZURE_GROUP_ACCOUNTS_NAME_RE = 'azure_group_accounts_name_re'
    AZURE_OAUTH_API_URL = 'azure_oauth_api_url'
    AZURE_OAUTH_AUTHORIZE_URL = 'azure_oauth_authorize_url'
    AZURE_OAUTH_AUTO_CONFIGURE = 'azure_oauth_auto_configure'
    AZURE_OAUTH_ENABLED = 'azure_oauth_enabled'
    AZURE_OAUTH_KEY = 'azure_oauth_key'
    AZURE_OAUTH_METADATA_URL = 'azure_oauth_metadata_url'
    AZURE_OAUTH_SCOPE = 'azure_oauth_scope'
    AZURE_OAUTH_SECRET = 'azure_oauth_secret'
    AZURE_OAUTH_TOKEN_URL = 'azure_oauth_token_url'
    AZURE_OPERATOR_GROUP = 'azure_operator_group'
    AZURE_SG_ENABLED = 'azure_sg_enabled'
    AZURE_USER_GROUP = 'azure_user_group'
    BG_DOMAIN_UPDATES = 'bg_domain_updates'
    BIND_ADDRESS = 'bind_address'
    CAPTCHA_ENABLE = 'captcha_enable'
    CAPTCHA_HEIGHT = 'captcha_height'
    CAPTCHA_LENGTH = 'captcha_length'
    CAPTCHA_SESSION_KEY = 'captcha_session_key'
    CAPTCHA_WIDTH = 'captcha_width'
    CSRF_COOKIE_SECURE = 'csrf_cookie_secure'
    CUSTOM_CSS = 'custom_css'
    CUSTOM_HISTORY_HEADER = 'custom_history_header'
    DEFAULT_DOMAIN_TABLE_SIZE = 'default_domain_table_size'
    DEFAULT_RECORD_TABLE_SIZE = 'default_record_table_size'
    DELETE_SSO_ACCOUNTS = 'delete_sso_accounts'
    DENY_DOMAIN_OVERRIDE = 'deny_domain_override'
    DNSSEC_ADMINS_ONLY = 'dnssec_admins_only'
    ENABLE_API_RR_HISTORY = 'enable_api_rr_history'
    ENFORCE_API_TTL = 'enforce_api_ttl'
    FORWARD_RECORDS_ALLOW_EDIT = 'forward_records_allow_edit'
    FULLSCREEN_LAYOUT = 'fullscreen_layout'
    GITHUB_OAUTH_API_URL = 'github_oauth_api_url'
    GITHUB_OAUTH_AUTHORIZE_URL = 'github_oauth_authorize_url'
    GITHUB_OAUTH_AUTO_CONFIGURE = 'github_oauth_auto_configure'
    GITHUB_OAUTH_ENABLED = 'github_oauth_enabled'
    GITHUB_OAUTH_KEY = 'github_oauth_key'
    GITHUB_OAUTH_METADATA_URL = 'github_oauth_metadata_url'
    GITHUB_OAUTH_SCOPE = 'github_oauth_scope'
    GITHUB_OAUTH_SECRET = 'github_oauth_secret'
    GITHUB_OAUTH_TOKEN_URL = 'github_oauth_token_url'
    GOOGLE_AUTHORIZE_URL = 'google_authorize_url'
    GOOGLE_BASE_URL = 'google_base_url'
    GOOGLE_OAUTH_AUTO_CONFIGURE = 'google_oauth_auto_configure'
    GOOGLE_OAUTH_ENABLED = 'google_oauth_enabled'
    GOOGLE_OAUTH_CLIENT_ID = 'google_oauth_client_id'
    GOOGLE_OAUTH_CLIENT_SECRET = 'google_oauth_client_secret'
    GOOGLE_OAUTH_METADATA_URL = 'google_oauth_metadata_url'
    GOOGLE_OAUTH_SCOPE = 'google_oauth_scope'
    GOOGLE_TOKEN_URL = 'google_token_url'
    GRAVATAR_ENABLED = 'gravatar_enabled'
    HSTS_ENABLED = 'hsts_enabled'
    LDAP_ADMIN_GROUP = 'ldap_admin_group'
    LDAP_ADMIN_PASSWORD = 'ldap_admin_password'
    LDAP_ADMIN_USERNAME = 'ldap_admin_username'
    LDAP_BASE_DN = 'ldap_base_dn'
    LDAP_DOMAIN = 'ldap_domain'
    LDAP_ENABLED = 'ldap_enabled'
    LDAP_FILTER_BASIC = 'ldap_filter_basic'
    LDAP_FILTER_GROUP = 'ldap_filter_group'
    LDAP_FILTER_GROUPNAME = 'ldap_filter_groupname'
    LDAP_FILTER_USERNAME = 'ldap_filter_username'
    LDAP_OPERATOR_GROUP = 'ldap_operator_group'
    LDAP_SG_ENABLED = 'ldap_sg_enabled'
    LDAP_TYPE = 'ldap_type'
    LDAP_URI = 'ldap_uri'
    LDAP_USER_GROUP = 'ldap_user_group'
    LOCAL_DB_ENABLED = 'local_db_enabled'
    LOGIN_LDAP_FIRST = 'login_ldap_first'
    LOG_LEVEL = 'log_level'
    MAIL_DEBUG = 'mail_debug'
    MAIL_DEFAULT_SENDER = 'mail_default_sender'
    MAIL_PASSWORD = 'mail_password'
    MAIL_PORT = 'mail_port'
    MAIL_SERVER = 'mail_server'
    MAIL_USERNAME = 'mail_username'
    MAIL_USE_SSL = 'mail_use_ssl'
    MAIL_USE_TLS = 'mail_use_tls'
    MAINTENANCE = 'maintenance'
    MAX_HISTORY_RECORDS = 'max_history_records'
    OIDC_OAUTH_ACCOUNT_DESCRIPTION_PROPERTY = 'oidc_oauth_account_description_property'
    OIDC_OAUTH_ACCOUNT_NAME_PROPERTY = 'oidc_oauth_account_name_property'
    OIDC_OAUTH_API_URL = 'oidc_oauth_api_url'
    OIDC_OAUTH_AUTHORIZE_URL = 'oidc_oauth_authorize_url'
    OIDC_OAUTH_AUTO_CONFIGURE = 'oidc_oauth_auto_configure'
    OIDC_OAUTH_EMAIL = 'oidc_oauth_email'
    OIDC_OAUTH_ENABLED = 'oidc_oauth_enabled'
    OIDC_OAUTH_FIRSTNAME = 'oidc_oauth_firstname'
    OIDC_OAUTH_KEY = 'oidc_oauth_key'
    OIDC_OAUTH_LAST_NAME = 'oidc_oauth_last_name'
    OIDC_OAUTH_LOGOUT_URL = 'oidc_oauth_logout_url'
    OIDC_OAUTH_METADATA_URL = 'oidc_oauth_metadata_url'
    OIDC_OAUTH_SECRET = 'oidc_oauth_secret'
    OIDC_OAUTH_SCOPE = 'oidc_oauth_scope'
    OIDC_OAUTH_TOKEN_URL = 'oidc_oauth_token_url'
    OIDC_OAUTH_USERNAME = 'oidc_oauth_username'
    OTP_FIELD_ENABLED = 'otp_field_enabled'
    OTP_FORCE = 'otp_force'
    PDNS_ADMIN_LOG_LEVEL = 'pdns_admin_log_level'
    PDNS_API_KEY = 'pdns_api_key'
    PDNS_API_TIMEOUT = 'pdns_api_timeout'
    PDNS_API_URL = 'pdns_api_url'
    PDNS_VERSION = 'pdns_version'
    PORT = 'port'
    PRESERVE_HISTORY = 'preserve_history'
    PRETTY_IPV6_PTR = 'pretty_ipv6_ptr'
    PURGE = 'purge'
    PWD_ENFORCE_CHARACTERS = 'pwd_enforce_characters'
    PWD_ENFORCE_COMPLEXITY = 'pwd_enforce_complexity'
    PWD_MIN_COMPLEXITY = 'pwd_min_complexity'
    PWD_MIN_LEN = 'pwd_min_len'
    PWD_MIN_LOWERCASE = 'pwd_min_lowercase'
    PWD_MIN_UPPERCASE = 'pwd_min_uppercase'
    PWD_MIN_DIGITS = 'pwd_min_digits'
    PWD_MIN_SPECIAL = 'pwd_min_special'
    RECORD_HELPER = 'record_helper'
    RECORD_QUICK_EDIT = 'record_quick_edit'
    REMOTE_USER_COOKIES = 'remote_user_cookies'
    REMOTE_USER_ENABLED = 'remote_user_enabled'
    REMOTE_USER_LOGOUT_URL = 'remote_user_logout_url'
    REVERSE_RECORDS_ALLOW_EDIT = 'reverse_records_allow_edit'
    SALT = 'salt'
    SAML_ASSERTION_ENCRYPTED = 'saml_assertion_encrypted'
    SAML_ATTRIBUTE_ACCOUNT = 'saml_attribute_account'
    SAML_ATTRIBUTE_ADMIN = 'saml_attribute_admin'
    SAML_ATTRIBUTE_EMAIL = 'saml_attribute_email'
    SAML_ATTRIBUTE_GIVENNAME = 'saml_attribute_givenname'
    SAML_ATTRIBUTE_GROUP = 'saml_attribute_group'
    SAML_ATTRIBUTE_NAME = 'saml_attribute_name'
    SAML_ATTRIBUTE_SURNAME = 'saml_attribute_surname'
    SAML_ATTRIBUTE_USERNAME = 'saml_attribute_username'
    SAML_CERT = 'saml_cert'
    SAML_DEBUG = 'saml_debug'
    SAML_ENABLED = 'saml_enabled'
    SAML_GROUP_ADMIN_NAME = 'saml_group_admin_name'
    SAML_GROUP_OPERATOR_NAME = 'saml_group_operator_name'
    SAML_GROUP_TO_ACCOUNT_MAPPING = 'saml_group_to_account_mapping'
    SAML_IDP_ENTITY_ID = 'saml_idp_entity_id'
    SAML_IDP_SSO_BINDING = 'saml_idp_sso_binding'
    SAML_KEY = 'saml_key'
    SAML_LOGOUT = 'saml_logout'
    SAML_LOGOUT_URL = 'saml_logout_url'
    SAML_METADATA_CACHE_LIFETIME = 'saml_metadata_cache_lifetime'
    SAML_METADATA_URL = 'saml_metadata_url'
    SAML_NAMEID_FORMAT = 'saml_nameid_format'
    SAML_PATH = 'saml_path'
    SAML_SIGN_REQUEST = 'saml_sign_request'
    SAML_SP_CONTACT_MAIL = 'saml_sp_contact_mail'
    SAML_SP_CONTACT_NAME = 'saml_sp_contact_name'
    SAML_SP_ENTITY_ID = 'saml_sp_entity_id'
    SAML_WANT_MESSAGE_SIGNED = 'saml_want_message_signed'
    SECRET_KEY = 'secret_key'
    SERVER_EXTERNAL_SSL = 'server_external_ssl'
    SESSION_COOKIE_SECURE = 'session_cookie_secure'
    SESSION_TIMEOUT = 'session_timeout'
    SESSION_TYPE = 'session_type'
    SIGNUP_ENABLED = 'signup_enabled'
    SITE_NAME = 'site_name'
    SITE_URL = 'site_url'
    SQLALCHEMY_DATABASE_URI = 'sqlalchemy_database_uri'
    SQLALCHEMY_ENGINE_OPTIONS = 'sqlalchemy_engine_options'
    SQLALCHEMY_TRACK_MODIFICATIONS = 'sqlalchemy_track_modifications'
    TTL_OPTIONS = 'ttl_options'
    URN_VALUE = 'urn_value'
    VERIFY_SSL_CONNECTIONS = 'verify_ssl_connections'
    VERIFY_USER_EMAIL = 'verify_user_email'
    WARN_SESSION_TIMEOUT = 'warn_session_timeout'


def init():
    global initialized
    if initialized:
        return

    inst.set(SettingMap.ACCOUNT_NAME_EXTRA_CHARS, Setting(**{
        'name': SettingMap.ACCOUNT_NAME_EXTRA_CHARS,
        'description': 'This determines if non-basic characters will be allowed in account names.',
        'label': 'Allow Non-Basic Characters in Account Names',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.ALLOW_USER_CREATE_DOMAIN, Setting(**{
        'name': SettingMap.ALLOW_USER_CREATE_DOMAIN,
        'description': 'This determines if users can create zones.',
        'label': 'Allow Users to Create Zones',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.ALLOW_USER_REMOVE_DOMAIN, Setting(**{
        'name': SettingMap.ALLOW_USER_REMOVE_DOMAIN,
        'description': 'This determines if users can remove zones.',
        'label': 'Allow Users to Remove Zones',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.ALLOW_USER_VIEW_HISTORY, Setting(**{
        'name': SettingMap.ALLOW_USER_VIEW_HISTORY,
        'description': 'This determines if users can view activity logs.',
        'label': 'Allow Users to View Activity Logs',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.AUTOPROVISIONING, Setting(**{
        'name': SettingMap.AUTOPROVISIONING,
        'description': 'This determines if LDAP role auto-provisioning is enabled.',
        'label': 'Auto-Provisioning',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.AUTOPROVISIONING_ATTRIBUTE, Setting(**{
        'name': SettingMap.AUTOPROVISIONING_ATTRIBUTE,
        'description': 'This defines the LDAP attribute to use for extracting user roles',
        'label': 'User Role LDAP Attribute',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.AUTO_PTR, Setting(**{
        'name': SettingMap.AUTO_PTR,
        'description': 'This determines if PTR records should be automatically created for A and AAAA records.',
        'label': 'Automatic PTR Setup',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.AZURE_ADMIN_GROUP, Setting(**{
        'name': SettingMap.AZURE_ADMIN_GROUP,
        'description': 'This defines the Azure AD group ID whose members will be granted admin access.',
        'label': 'Azure Admin Group',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.AZURE_GROUP_ACCOUNTS_DESCRIPTION, Setting(**{
        'name': SettingMap.AZURE_GROUP_ACCOUNTS_DESCRIPTION,
        'description': 'This defines the Azure AD group claim to use for extracting group descriptions.',
        'label': 'Azure Group Description Claim',
        'stype': str,
        'default': 'description',
    }))

    inst.set(SettingMap.AZURE_GROUP_ACCOUNTS_DESCRIPTION_RE, Setting(**{
        'name': SettingMap.AZURE_GROUP_ACCOUNTS_DESCRIPTION_RE,
        'description': 'This defines the regular expression to use for extracting group descriptions.',
        'label': 'Azure Group Description Regular Expression',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.AZURE_GROUP_ACCOUNTS_ENABLED, Setting(**{
        'name': SettingMap.AZURE_GROUP_ACCOUNTS_ENABLED,
        'description': 'This determines if Azure AD groups should be translated into PDA accounts.',
        'label': 'Azure Group Account Synchronization',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.AZURE_GROUP_ACCOUNTS_NAME, Setting(**{
        'name': SettingMap.AZURE_GROUP_ACCOUNTS_NAME,
        'description': 'This defines the Azure AD group claim to use for extracting group names.',
        'label': 'Azure Group Name Claim',
        'stype': str,
        'default': 'displayName',
    }))

    inst.set(SettingMap.AZURE_GROUP_ACCOUNTS_NAME_RE, Setting(**{
        'name': SettingMap.AZURE_GROUP_ACCOUNTS_NAME_RE,
        'description': 'This defines the regular expression to use for extracting group names.',
        'label': 'Azure Group Name Regular Expression',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.AZURE_OAUTH_API_URL, Setting(**{
        'name': SettingMap.AZURE_OAUTH_API_URL,
        'description': 'This defines the Azure AD OAuth API URL.',
        'label': 'Azure OAuth API URL',
        'stype': str,
        'default': 'https://graph.microsoft.com/v1.0/',
    }))

    inst.set(SettingMap.AZURE_OAUTH_AUTHORIZE_URL, Setting(**{
        'name': SettingMap.AZURE_OAUTH_AUTHORIZE_URL,
        'description': 'This defines the Azure AD OAuth authorize URL.',
        'label': 'Azure OAuth Authorize URL',
        'stype': str,
        'default': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
    }))

    inst.set(SettingMap.AZURE_OAUTH_AUTO_CONFIGURE, Setting(**{
        'name': SettingMap.AZURE_OAUTH_AUTO_CONFIGURE,
        'description': 'This determines if Azure AD OAuth should be automatically configured from a metadata URL.',
        'label': 'Azure OAuth Auto-Configuration',
        'stype': bool,
        'default': True,
    }))

    inst.set(SettingMap.AZURE_OAUTH_ENABLED, Setting(**{
        'name': SettingMap.AZURE_OAUTH_ENABLED,
        'description': 'This determines if Azure AD OAuth should be enabled.',
        'label': 'Azure OAuth',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.AZURE_OAUTH_KEY, Setting(**{
        'name': SettingMap.AZURE_OAUTH_KEY,
        'description': 'This defines the Azure AD OAuth client key.',
        'label': 'Azure OAuth Client Key',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.AZURE_OAUTH_METADATA_URL, Setting(**{
        'name': SettingMap.AZURE_OAUTH_METADATA_URL,
        'description': 'This defines the Azure AD OAuth metadata URL.',
        'label': 'Azure OAuth Metadata URL',
        'stype': str,
        'default': 'https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration',
    }))

    inst.set(SettingMap.AZURE_OAUTH_SCOPE, Setting(**{
        'name': SettingMap.AZURE_OAUTH_SCOPE,
        'description': 'This defines the Azure AD OAuth scopes to request.',
        'label': 'Azure OAuth Scopes',
        'stype': str,
        'default': 'User.Read openid email profile',
    }))

    inst.set(SettingMap.AZURE_OAUTH_SECRET, Setting(**{
        'name': SettingMap.AZURE_OAUTH_SECRET,
        'description': 'This defines the Azure AD OAuth client secret.',
        'label': 'Azure OAuth Client Secret',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.AZURE_OAUTH_TOKEN_URL, Setting(**{
        'name': SettingMap.AZURE_OAUTH_TOKEN_URL,
        'description': 'This defines the Azure AD OAuth token URL.',
        'label': 'Azure OAuth Token URL',
        'stype': str,
        'default': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
    }))

    inst.set(SettingMap.AZURE_OPERATOR_GROUP, Setting(**{
        'name': SettingMap.AZURE_OPERATOR_GROUP,
        'description': 'This defines the Azure AD group ID whose members will be granted operator access.',
        'label': 'Azure Operator Group',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.AZURE_SG_ENABLED, Setting(**{
        'name': SettingMap.AZURE_SG_ENABLED,
        'description': 'This determines if specifically defined Azure AD groups should be used to select PDA user '
                       'roles.',
        'label': 'Azure Group Security',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.AZURE_USER_GROUP, Setting(**{
        'name': SettingMap.AZURE_USER_GROUP,
        'description': 'This defines the Azure AD group ID whose members will be granted user access.',
        'label': 'Azure User Group Claim',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.BG_DOMAIN_UPDATES, Setting(**{
        'name': SettingMap.BG_DOMAIN_UPDATES,
        'description': 'This determines if zone updates should be performed in the background or foreground of user '
                       'requests.',
        'label': 'Background Zone Updates',
        'stype': bool,
        'default': True,
    }))

    inst.set(SettingMap.BIND_ADDRESS, Setting(**{
        'name': SettingMap.BIND_ADDRESS,
        'description': 'This defines the address to bind the PDA HTTP server to.',
        'label': 'Bind Address',
        'stype': str,
        'default': '0.0.0.0',
    }))

    inst.set(SettingMap.CAPTCHA_ENABLE, Setting(**{
        'name': SettingMap.CAPTCHA_ENABLE,
        'description': 'This determines if CAPTCHA should be enabled for user login and registration.',
        'label': 'CAPTCHA',
        'stype': bool,
        'default': True,
    }))

    inst.set(SettingMap.CAPTCHA_HEIGHT, Setting(**{
        'name': SettingMap.CAPTCHA_HEIGHT,
        'description': 'This defines the height of the CAPTCHA image.',
        'label': 'CAPTCHA Height',
        'stype': int,
        'default': 50,
    }))

    inst.set(SettingMap.CAPTCHA_LENGTH, Setting(**{
        'name': SettingMap.CAPTCHA_LENGTH,
        'description': 'This defines the length of the CAPTCHA text.',
        'label': 'CAPTCHA Length',
        'stype': int,
        'default': 6,
    }))

    inst.set(SettingMap.CAPTCHA_SESSION_KEY, Setting(**{
        'name': SettingMap.CAPTCHA_SESSION_KEY,
        'description': 'This defines the session key to use for storing CAPTCHA data.',
        'label': 'CAPTCHA Session Key',
        'stype': str,
        'default': 'captcha_image',
    }))

    inst.set(SettingMap.CAPTCHA_WIDTH, Setting(**{
        'name': SettingMap.CAPTCHA_WIDTH,
        'description': 'This defines the width of the CAPTCHA image.',
        'label': 'CAPTCHA Width',
        'stype': int,
        'default': 160,
    }))

    inst.set(SettingMap.CSRF_COOKIE_SECURE, Setting(**{
        'name': SettingMap.CSRF_COOKIE_SECURE,
        'description': 'This determines if the CSRF cookie should be marked as secure.',
        'label': 'CSRF Cookie Secure',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.CUSTOM_CSS, Setting(**{
        'name': SettingMap.CUSTOM_CSS,
        'description': 'This defines the URL of custom CSS to be included in the PDA web interface.',
        'label': 'Custom CSS',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.CUSTOM_HISTORY_HEADER, Setting(**{
        'name': SettingMap.CUSTOM_HISTORY_HEADER,
        'description': 'This defines the HTTP header to be used for custom activity logs.',
        'label': 'Custom Activity Log HTTP Header',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.DEFAULT_DOMAIN_TABLE_SIZE, Setting(**{
        'name': SettingMap.DEFAULT_DOMAIN_TABLE_SIZE,
        'description': 'This defines the default number of zones to display per page in the zone list view.',
        'label': 'Default Zone List Size',
        'stype': int,
        'default': 10,
    }))

    inst.set(SettingMap.DEFAULT_RECORD_TABLE_SIZE, Setting(**{
        'name': SettingMap.DEFAULT_RECORD_TABLE_SIZE,
        'description': 'This defines the default number of records to display per page in the zone editor view.',
        'label': 'Default Zone Editor Record List Size',
        'stype': int,
        'default': 15,
    }))

    inst.set(SettingMap.DELETE_SSO_ACCOUNTS, Setting(**{
        'name': SettingMap.DELETE_SSO_ACCOUNTS,
        'description': 'This determines if PDA user account associations should be removed based on missing OIDC '
                       'associations.',
        'label': 'OIDC PDA Account Cleanup',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.DENY_DOMAIN_OVERRIDE, Setting(**{
        'name': SettingMap.DENY_DOMAIN_OVERRIDE,
        'description': 'This determines whether to deny zone modification requests, that would create a DNS conflict '
                       'through pre-existing records of another zone.',
        'label': 'Deny Zone Conflict Requests',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.DNSSEC_ADMINS_ONLY, Setting(**{
        'name': SettingMap.DNSSEC_ADMINS_ONLY,
        'description': 'This determines if DNSSEC key management should be restricted to PDA administrators only.',
        'label': 'DNSSEC by Admins Only',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.ENABLE_API_RR_HISTORY, Setting(**{
        'name': SettingMap.ENABLE_API_RR_HISTORY,
        'description': 'This determines if the API should record zone activity for each record modification.',
        'label': 'API Record Activity Tracking',
        'stype': bool,
        'default': True,
    }))

    inst.set(SettingMap.ENFORCE_API_TTL, Setting(**{
        'name': SettingMap.ENFORCE_API_TTL,
        'description': 'This determines if the API should require that a record must have a TTL defined from the '
                       'pre-defined options in the "ttl_options" setting.',
        'label': 'Enforce API TTL',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.FORWARD_RECORDS_ALLOW_EDIT, Setting(**{
        'name': SettingMap.FORWARD_RECORDS_ALLOW_EDIT,
        'description': 'This defines a map of forward zone record types with flags indicating if the record type '
                       'should be selectable in the zone editor.',
        'label': 'Forward Zone Record Types',
        'stype': dict,
        'default': {
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
            'URI': False,
        },
    }))

    inst.set(SettingMap.FULLSCREEN_LAYOUT, Setting(**{
        'name': SettingMap.FULLSCREEN_LAYOUT,
        'description': 'This determines if the PDA web interface should use a fullscreen or boxed layout.',
        'label': 'Fullscreen Layout',
        'stype': bool,
        'default': True,
    }))

    inst.set(SettingMap.GITHUB_OAUTH_API_URL, Setting(**{
        'name': SettingMap.GITHUB_OAUTH_API_URL,
        'description': 'This defines the URL of the GitHub OAuth API.',
        'label': 'GitHub OAuth API URL',
        'stype': str,
        'default': 'https://api.github.com/user',
    }))

    inst.set(SettingMap.GITHUB_OAUTH_AUTHORIZE_URL, Setting(**{
        'name': SettingMap.GITHUB_OAUTH_AUTHORIZE_URL,
        'description': 'This defines the URL of the GitHub OAuth authorization endpoint.',
        'label': 'GitHub OAuth Authorization URL',
        'stype': str,
        'default': 'https://github.com/login/oauth/authorize',
    }))

    inst.set(SettingMap.GITHUB_OAUTH_AUTO_CONFIGURE, Setting(**{
        'name': SettingMap.GITHUB_OAUTH_AUTO_CONFIGURE,
        'description': 'This determines if the GitHub OAuth provider should be automatically configured using a '
                       'metadata URL.',
        'label': 'GitHub OAuth Automatic Configuration',
        'stype': bool,
        'default': True,
    }))

    inst.set(SettingMap.GITHUB_OAUTH_ENABLED, Setting(**{
        'name': SettingMap.GITHUB_OAUTH_ENABLED,
        'description': 'This determines if the GitHub OAuth provider should be enabled.',
        'label': 'GitHub OAuth Provider',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.GITHUB_OAUTH_KEY, Setting(**{
        'name': SettingMap.GITHUB_OAUTH_KEY,
        'description': 'This defines the GitHub OAuth client ID.',
        'label': 'GitHub OAuth Client ID',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.GITHUB_OAUTH_METADATA_URL, Setting(**{
        'name': SettingMap.GITHUB_OAUTH_METADATA_URL,
        'description': 'This defines the URL of the GitHub OAuth metadata endpoint.',
        'label': 'GitHub OAuth Metadata URL',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.GITHUB_OAUTH_SCOPE, Setting(**{
        'name': SettingMap.GITHUB_OAUTH_SCOPE,
        'description': 'This defines the GitHub OAuth scopes to be requested.',
        'label': 'GitHub OAuth Scopes',
        'stype': str,
        'default': 'email',
    }))

    inst.set(SettingMap.GITHUB_OAUTH_SECRET, Setting(**{
        'name': SettingMap.GITHUB_OAUTH_SECRET,
        'description': 'This defines the GitHub OAuth client secret.',
        'label': 'GitHub OAuth Client Secret',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.GITHUB_OAUTH_TOKEN_URL, Setting(**{
        'name': SettingMap.GITHUB_OAUTH_TOKEN_URL,
        'description': 'This defines the URL of the GitHub OAuth token endpoint.',
        'label': 'GitHub OAuth Token URL',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.GOOGLE_AUTHORIZE_URL, Setting(**{
        'name': SettingMap.GOOGLE_AUTHORIZE_URL,
        'description': 'This defines the URL of the Google OAuth authorization endpoint.',
        'label': 'Google OAuth Authorization URL',
        'stype': str,
        'default': 'https://accounts.google.com/o/oauth2/v2/auth',
    }))

    inst.set(SettingMap.GOOGLE_BASE_URL, Setting(**{
        'name': SettingMap.GOOGLE_BASE_URL,
        'description': 'This defines the base URL of the Google OAuth API.',
        'label': 'Google OAuth API Base URL',
        'stype': str,
        'default': 'https://www.googleapis.com/oauth2/v3/',
    }))

    inst.set(SettingMap.GOOGLE_OAUTH_AUTO_CONFIGURE, Setting(**{
        'name': SettingMap.GOOGLE_OAUTH_AUTO_CONFIGURE,
        'description': 'This determines if the Google OAuth provider should be automatically configured using a '
                       'metadata URL.',
        'label': 'Google OAuth Automatic Configuration',
        'stype': bool,
        'default': True,
    }))

    inst.set(SettingMap.GOOGLE_OAUTH_ENABLED, Setting(**{
        'name': SettingMap.GOOGLE_OAUTH_ENABLED,
        'description': 'This determines if the Google OAuth provider should be enabled.',
        'label': 'Google OAuth Provider',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.GOOGLE_OAUTH_CLIENT_ID, Setting(**{
        'name': SettingMap.GOOGLE_OAUTH_CLIENT_ID,
        'description': 'This defines the Google OAuth client ID.',
        'label': 'Google OAuth Client ID',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.GOOGLE_OAUTH_CLIENT_SECRET, Setting(**{
        'name': SettingMap.GOOGLE_OAUTH_CLIENT_SECRET,
        'description': 'This defines the Google OAuth client secret.',
        'label': 'Google OAuth Client Secret',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.GOOGLE_OAUTH_METADATA_URL, Setting(**{
        'name': SettingMap.GOOGLE_OAUTH_METADATA_URL,
        'description': 'This defines the URL of the Google OAuth metadata endpoint.',
        'label': 'Google OAuth Metadata URL',
        'stype': str,
        'default': 'https://accounts.google.com/.well-known/openid-configuration',
    }))

    inst.set(SettingMap.GOOGLE_OAUTH_SCOPE, Setting(**{
        'name': SettingMap.GOOGLE_OAUTH_SCOPE,
        'description': 'This defines the Google OAuth scopes to be requested.',
        'label': 'Google OAuth Scopes',
        'stype': str,
        'default': 'openid email profile',
    }))

    inst.set(SettingMap.GOOGLE_TOKEN_URL, Setting(**{
        'name': SettingMap.GOOGLE_TOKEN_URL,
        'description': 'This defines the URL of the Google OAuth token endpoint.',
        'label': 'Google OAuth Token URL',
        'stype': str,
        'default': 'https://oauth2.googleapis.com/token',
    }))

    inst.set(SettingMap.GRAVATAR_ENABLED, Setting(**{
        'name': SettingMap.GRAVATAR_ENABLED,
        'description': 'This determines if Gravatar should be used to retrieve user avatars.',
        'label': 'Gravatar',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.HSTS_ENABLED, Setting(**{
        'name': SettingMap.HSTS_ENABLED,
        'description': 'This determines if HTTP Strict Transport Security should be enabled.',
        'label': 'HTTP Strict Transport Security',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.LDAP_ADMIN_GROUP, Setting(**{
        'name': SettingMap.LDAP_ADMIN_GROUP,
        'description': 'This defines the LDAP group that will be granted administrator privileges.',
        'label': 'LDAP Administrator Group',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.LDAP_ADMIN_PASSWORD, Setting(**{
        'name': SettingMap.LDAP_ADMIN_PASSWORD,
        'description': 'This defines the password of the LDAP administrator account.',
        'label': 'LDAP Administrator Password',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.LDAP_ADMIN_USERNAME, Setting(**{
        'name': SettingMap.LDAP_ADMIN_USERNAME,
        'description': 'This defines the username of the LDAP administrator account.',
        'label': 'LDAP Administrator Username',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.LDAP_BASE_DN, Setting(**{
        'name': SettingMap.LDAP_BASE_DN,
        'description': 'This defines the base DN of the LDAP directory.',
        'label': 'LDAP Base DN',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.LDAP_DOMAIN, Setting(**{
        'name': SettingMap.LDAP_DOMAIN,
        'description': 'This defines the Active Directory domain of the LDAP server.',
        'label': 'Active Directory Domain',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.LDAP_ENABLED, Setting(**{
        'name': SettingMap.LDAP_ENABLED,
        'description': 'This determines if LDAP authentication should be enabled.',
        'label': 'LDAP Authentication',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.LDAP_FILTER_BASIC, Setting(**{
        'name': SettingMap.LDAP_FILTER_BASIC,
        'description': 'This defines the LDAP filter used to retrieve user information.',
        'label': 'LDAP Basic Filter',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.LDAP_FILTER_GROUP, Setting(**{
        'name': SettingMap.LDAP_FILTER_GROUP,
        'description': 'This defines the LDAP filter used to retrieve group membership information.',
        'label': 'LDAP Group Filter',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.LDAP_FILTER_GROUPNAME, Setting(**{
        'name': SettingMap.LDAP_FILTER_GROUPNAME,
        'description': 'This defines the LDAP filter used to retrieve group name information.',
        'label': 'LDAP Group Name Filter',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.LDAP_FILTER_USERNAME, Setting(**{
        'name': SettingMap.LDAP_FILTER_USERNAME,
        'description': 'This defines the LDAP filter used to retrieve username information.',
        'label': 'LDAP Username Filter',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.LDAP_OPERATOR_GROUP, Setting(**{
        'name': SettingMap.LDAP_OPERATOR_GROUP,
        'description': 'This defines the LDAP group filter to be used for granting operator privileges.',
        'label': 'LDAP Operator Group Filter',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.LDAP_SG_ENABLED, Setting(**{
        'name': SettingMap.LDAP_SG_ENABLED,
        'description': 'This determines if LDAP filters should be used to map LDAP users to PDA user roles.',
        'label': 'LDAP Security Group Mapping',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.LDAP_TYPE, Setting(**{
        'name': SettingMap.LDAP_TYPE,
        'description': 'This defines the type of LDAP server to be used.',
        'label': 'LDAP Type',
        'stype': str,
        'default': 'ldap',
    }))

    inst.set(SettingMap.LDAP_URI, Setting(**{
        'name': SettingMap.LDAP_URI,
        'description': 'This defines the URI of the LDAP server.',
        'label': 'LDAP URI',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.LDAP_USER_GROUP, Setting(**{
        'name': SettingMap.LDAP_USER_GROUP,
        'description': 'This defines the LDAP group filter to be used for granting user privileges.',
        'label': 'LDAP User Group Filter',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.LOCAL_DB_ENABLED, Setting(**{
        'name': SettingMap.LOCAL_DB_ENABLED,
        'description': 'This determines whether users can authenticate with accounts in the local PDA database.',
        'label': 'Local User Authentication',
        'stype': bool,
        'default': True,
    }))

    inst.set(SettingMap.LOGIN_LDAP_FIRST, Setting(**{
        'name': SettingMap.LOGIN_LDAP_FIRST,
        'description': 'This determines if the LDAP authentication option should be selected by default on the login '
                       'screen when LDAP is enabled.',
        'label': 'Default To LDAP Authentication',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.LOG_LEVEL, Setting(**{
        'name': SettingMap.LOG_LEVEL,
        'description': 'This defines the logging level of the application.',
        'label': 'Logging Level',
        'stype': str,
        'default': 'WARNING',
    }))

    inst.set(SettingMap.MAIL_DEBUG, Setting(**{
        'name': SettingMap.MAIL_DEBUG,
        'description': 'This determines if email debugging should be enabled.',
        'label': 'Email Debugging',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.MAIL_DEFAULT_SENDER, Setting(**{
        'name': SettingMap.MAIL_DEFAULT_SENDER,
        'description': 'This defines the default sender of emails.',
        'label': 'Default Email Sender',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.MAIL_PASSWORD, Setting(**{
        'name': SettingMap.MAIL_PASSWORD,
        'description': 'This defines the password of the email account.',
        'label': 'Email Password',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.MAIL_PORT, Setting(**{
        'name': SettingMap.MAIL_PORT,
        'description': 'This defines the port of the email server.',
        'label': 'Email Port',
        'stype': int,
        'default': 25,
    }))

    inst.set(SettingMap.MAIL_SERVER, Setting(**{
        'name': SettingMap.MAIL_SERVER,
        'description': 'This defines the email server hostname or IP address.',
        'label': 'Email Server',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.MAIL_USERNAME, Setting(**{
        'name': SettingMap.MAIL_USERNAME,
        'description': 'This defines the username of the email account.',
        'label': 'Email Username',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.MAIL_USE_SSL, Setting(**{
        'name': SettingMap.MAIL_USE_SSL,
        'description': 'This determines if SSL should be used when connecting to the email server.',
        'label': 'Use SSL',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.MAIL_USE_TLS, Setting(**{
        'name': SettingMap.MAIL_USE_TLS,
        'description': 'This determines if TLS should be used when connecting to the email server.',
        'label': 'Use TLS',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.MAINTENANCE, Setting(**{
        'name': SettingMap.MAINTENANCE,
        'description': 'This determines if the application is in maintenance mode.',
        'label': 'Maintenance Mode',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.MAX_HISTORY_RECORDS, Setting(**{
        'name': SettingMap.MAX_HISTORY_RECORDS,
        'description': 'This defines the maximum number of activity records to be loaded in the activity auditor.',
        'label': 'Maximum Activity Records Loaded',
        'stype': int,
        'default': 1000,
    }))

    inst.set(SettingMap.OIDC_OAUTH_ACCOUNT_DESCRIPTION_PROPERTY, Setting(**{
        'name': SettingMap.OIDC_OAUTH_ACCOUNT_DESCRIPTION_PROPERTY,
        'description': 'This defines the account description field of the OpenID Connect application.',
        'label': 'OpenID Connect Account Description Field',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.OIDC_OAUTH_ACCOUNT_NAME_PROPERTY, Setting(**{
        'name': SettingMap.OIDC_OAUTH_ACCOUNT_NAME_PROPERTY,
        'description': 'This defines the account name field of the OpenID Connect application.',
        'label': 'OpenID Connect Account Name Field',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.OIDC_OAUTH_API_URL, Setting(**{
        'name': SettingMap.OIDC_OAUTH_API_URL,
        'description': 'This defines the API URL of the OpenID Connect application.',
        'label': 'OpenID Connect API URL',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.OIDC_OAUTH_AUTHORIZE_URL, Setting(**{
        'name': SettingMap.OIDC_OAUTH_AUTHORIZE_URL,
        'description': 'This defines the authorization URL of the OpenID Connect application.',
        'label': 'OpenID Connect Authorization URL',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.OIDC_OAUTH_AUTO_CONFIGURE, Setting(**{
        'name': SettingMap.OIDC_OAUTH_AUTO_CONFIGURE,
        'description': 'This determines if the OpenID Connect application should be automatically configured using a '
                       'metadata URL.',
        'label': 'OpenID Connect Automatic Configuration',
        'stype': bool,
        'default': True,
    }))

    inst.set(SettingMap.OIDC_OAUTH_EMAIL, Setting(**{
        'name': SettingMap.OIDC_OAUTH_EMAIL,
        'description': 'This defines the email field of the OpenID Connect application.',
        'label': 'OpenID Connect Email Field',
        'stype': str,
        'default': 'email',
    }))

    inst.set(SettingMap.OIDC_OAUTH_ENABLED, Setting(**{
        'name': SettingMap.OIDC_OAUTH_ENABLED,
        'description': 'This determines if OpenID Connect authentication should be enabled.',
        'label': 'OpenID Connect Authentication',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.OIDC_OAUTH_FIRSTNAME, Setting(**{
        'name': SettingMap.OIDC_OAUTH_FIRSTNAME,
        'description': 'This defines the first name field of the OpenID Connect application.',
        'label': 'OpenID Connect First Name Field',
        'stype': str,
        'default': 'given_name',
    }))

    inst.set(SettingMap.OIDC_OAUTH_KEY, Setting(**{
        'name': SettingMap.OIDC_OAUTH_KEY,
        'description': 'This defines the client ID of the OpenID Connect application.',
        'label': 'OpenID Connect Client ID',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.OIDC_OAUTH_LAST_NAME, Setting(**{
        'name': SettingMap.OIDC_OAUTH_LAST_NAME,
        'description': 'This defines the last name field of the OpenID Connect application.',
        'label': 'OpenID Connect Last Name Field',
        'stype': str,
        'default': 'family_name',
    }))

    inst.set(SettingMap.OIDC_OAUTH_LOGOUT_URL, Setting(**{
        'name': SettingMap.OIDC_OAUTH_LOGOUT_URL,
        'description': 'This defines the logout URL of the OpenID Connect application.',
        'label': 'OpenID Connect Logout URL',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.OIDC_OAUTH_METADATA_URL, Setting(**{
        'name': SettingMap.OIDC_OAUTH_METADATA_URL,
        'description': 'This defines the metadata URL of the OpenID Connect application.',
        'label': 'OpenID Connect Metadata URL',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.OIDC_OAUTH_SECRET, Setting(**{
        'name': SettingMap.OIDC_OAUTH_SECRET,
        'description': 'This defines the client secret of the OpenID Connect application.',
        'label': 'OpenID Connect Client Secret',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.OIDC_OAUTH_SCOPE, Setting(**{
        'name': SettingMap.OIDC_OAUTH_SCOPE,
        'description': 'This defines the requested scopes of the OpenID Connect application.',
        'label': 'OpenID Connect Scope',
        'stype': str,
        'default': 'email',
    }))

    inst.set(SettingMap.OIDC_OAUTH_TOKEN_URL, Setting(**{
        'name': SettingMap.OIDC_OAUTH_TOKEN_URL,
        'description': 'This defines the token URL of the OpenID Connect application.',
        'label': 'OpenID Connect Token URL',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.OIDC_OAUTH_USERNAME, Setting(**{
        'name': SettingMap.OIDC_OAUTH_USERNAME,
        'description': 'This defines the username field of the OpenID Connect application.',
        'label': 'OpenID Connect Username Field',
        'stype': str,
        'default': 'preferred_username',
    }))

    inst.set(SettingMap.OTP_FIELD_ENABLED, Setting(**{
        'name': SettingMap.OTP_FIELD_ENABLED,
        'description': 'This determines if the OTP feature should be enabled.',
        'label': 'OTP Field',
        'stype': bool,
        'default': True,
    }))

    inst.set(SettingMap.OTP_FORCE, Setting(**{
        'name': SettingMap.OTP_FORCE,
        'description': 'This determines if the OTP feature should be enforced.',
        'label': 'Force OTP',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.PDNS_ADMIN_LOG_LEVEL, Setting(**{
        'name': SettingMap.PDNS_ADMIN_LOG_LEVEL,
        'description': 'This defines the log level of the application.',
        'label': 'Log Level',
        'stype': str,
        'default': 'WARNING',
    }))

    inst.set(SettingMap.PDNS_API_KEY, Setting(**{
        'name': SettingMap.PDNS_API_KEY,
        'description': 'This defines the API key of the PowerDNS Authoritative server API.',
        'label': 'API Key',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.PDNS_API_TIMEOUT, Setting(**{
        'name': SettingMap.PDNS_API_TIMEOUT,
        'description': 'This defines the timeout (in seconds) of PowerDNS API requests.',
        'label': 'API Timeout',
        'stype': int,
        'default': 30,
    }))

    inst.set(SettingMap.PDNS_API_URL, Setting(**{
        'name': SettingMap.PDNS_API_URL,
        'description': 'This defines the URL of the PowerDNS Authoritative server API.',
        'label': 'API URL',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.PDNS_VERSION, Setting(**{
        'name': SettingMap.PDNS_VERSION,
        'description': 'This defines the version of the PowerDNS Authoritative server.',
        'label': 'PowerDNS Version',
        'stype': str,
        'default': '4.1.1',
    }))

    inst.set(SettingMap.PORT, Setting(**{
        'name': SettingMap.PORT,
        'description': 'This defines the port that the application\'s HTTP server should bind to.',
        'label': 'Port',
        'stype': int,
        'default': 9191,
    }))

    inst.set(SettingMap.PRESERVE_HISTORY, Setting(**{
        'name': SettingMap.PRESERVE_HISTORY,
        'description': 'This determines whether zone activity logs should be retained following zone removal.',
        'label': 'Preserve Activity Logs',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.PRETTY_IPV6_PTR, Setting(**{
        'name': SettingMap.PRETTY_IPV6_PTR,
        'description': 'This determines whether IPv6 PTR records should be displayed in a more pleasant format.',
        'label': 'Pretty IPv6 PTR',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.PURGE, Setting(**{
        'name': SettingMap.PURGE,
        'description': 'This determines whether PDA user roles should be purged when no roles were found using LDAP '
                       'role auto-provisioning.',
        'label': 'LDAP Purge User Roles',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.PWD_ENFORCE_CHARACTERS, Setting(**{
        'name': SettingMap.PWD_ENFORCE_CHARACTERS,
        'description': 'This determines whether the password policy should enforce the use of specific character '
                       'combinations.',
        'label': 'Enforce Password Character Policy',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.PWD_ENFORCE_COMPLEXITY, Setting(**{
        'name': SettingMap.PWD_ENFORCE_COMPLEXITY,
        'description': 'This determines whether the password policy should enforce the use of complex passwords.',
        'label': 'Enforce Password Complexity Policy',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.PWD_MIN_COMPLEXITY, Setting(**{
        'name': SettingMap.PWD_MIN_COMPLEXITY,
        'description': 'This defines the minimum complexity score required for a user password. The complexity score '
                       'is calculated using the zxcvbn library. The default value of the log factor is 11 as it is '
                       'considered secure.',
        'label': 'Minimum Password Complexity',
        'stype': int,
        'default': 11,
    }))

    inst.set(SettingMap.PWD_MIN_LEN, Setting(**{
        'name': SettingMap.PWD_MIN_LEN,
        'description': 'This defines the minimum length of a user password.',
        'label': 'Minimum Password Length',
        'stype': int,
        'default': 10,
    }))

    inst.set(SettingMap.PWD_MIN_LOWERCASE, Setting(**{
        'name': SettingMap.PWD_MIN_LOWERCASE,
        'description': 'This defines the minimum number of lowercase characters required for a user password.',
        'label': 'Minimum Lowercase Characters',
        'stype': int,
        'default': 3,
    }))

    inst.set(SettingMap.PWD_MIN_UPPERCASE, Setting(**{
        'name': SettingMap.PWD_MIN_UPPERCASE,
        'description': 'This defines the minimum number of uppercase characters required for a user password.',
        'label': 'Minimum Uppercase Characters',
        'stype': int,
        'default': 2,
    }))

    inst.set(SettingMap.PWD_MIN_DIGITS, Setting(**{
        'name': SettingMap.PWD_MIN_DIGITS,
        'description': 'This defines the minimum number of digits required for a user password.',
        'label': 'Minimum Digits',
        'stype': int,
        'default': 2,
    }))

    inst.set(SettingMap.PWD_MIN_SPECIAL, Setting(**{
        'name': SettingMap.PWD_MIN_SPECIAL,
        'description': 'This defines the minimum number of special characters required for a user password.',
        'label': 'Minimum Special Characters',
        'stype': int,
        'default': 1,
    }))

    inst.set(SettingMap.RECORD_HELPER, Setting(**{
        'name': SettingMap.RECORD_HELPER,
        'description': 'This determines whether the record helper should be enabled in the zone editor.',
        'label': 'Zone Editor Record Helper',
        'stype': bool,
        'default': True,
    }))

    inst.set(SettingMap.RECORD_QUICK_EDIT, Setting(**{
        'name': SettingMap.RECORD_QUICK_EDIT,
        'description': 'This determines whether the record quick edit feature should be enabled in the zone editor.',
        'label': 'Zone Editor Record Quick Edit',
        'stype': bool,
        'default': True,
    }))

    inst.set(SettingMap.REMOTE_USER_COOKIES, Setting(**{
        'name': SettingMap.REMOTE_USER_COOKIES,
        'description': 'This defines the name of the remote authentication cookies that should be destroyed during '
                       'logout.',
        'label': 'Remote Authentication Cookies',
        'stype': list,
        'default': [],
    }))

    inst.set(SettingMap.REMOTE_USER_ENABLED, Setting(**{
        'name': SettingMap.REMOTE_USER_ENABLED,
        'description': 'This determines whether remote user authentication should be enabled.',
        'label': 'Remote User Authentication',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.REMOTE_USER_LOGOUT_URL, Setting(**{
        'name': SettingMap.REMOTE_USER_LOGOUT_URL,
        'description': 'This defines the URL that the user should be redirected to after logging out.',
        'label': 'Remote User Logout URL',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.REVERSE_RECORDS_ALLOW_EDIT, Setting(**{
        'name': SettingMap.REVERSE_RECORDS_ALLOW_EDIT,
        'description': 'This defines a map of reverse zone record types with flags indicating if the record type '
                       'should be selectable in the zone editor.',
        'label': 'Reverse Zone Record Types',
        'stype': dict,
        'default': {
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
            'URI': False,
        },
    }))

    inst.set(SettingMap.SALT, Setting(**{
        'name': SettingMap.SALT,
        'description': 'This defines the salt used for password hashing.',
        'label': 'Password Hashing Salt',
        'stype': str,
        'default': '$2b$12$yLUMTIfl21FKJQpTkRQXCu',
    }))

    inst.set(SettingMap.SAML_ASSERTION_ENCRYPTED, Setting(**{
        'name': SettingMap.SAML_ASSERTION_ENCRYPTED,
        'description': 'This determines whether the SAML assertion should be encrypted.',
        'label': 'SAML Assertion Encrypted',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.SAML_ATTRIBUTE_ACCOUNT, Setting(**{
        'name': SettingMap.SAML_ATTRIBUTE_ACCOUNT,
        'description': 'This defines the SAML attribute that should be used for the account name.',
        'label': 'SAML Account Attribute',
        'stype': str,
        'default': None,
    }))

    inst.set(SettingMap.SAML_ATTRIBUTE_ADMIN, Setting(**{
        'name': SettingMap.SAML_ATTRIBUTE_ADMIN,
        'description': 'This defines the SAML attribute that should be used for the admin flag.',
        'label': 'SAML Admin Attribute',
        'stype': str,
        'default': None,
    }))

    inst.set(SettingMap.SAML_ATTRIBUTE_EMAIL, Setting(**{
        'name': SettingMap.SAML_ATTRIBUTE_EMAIL,
        'description': 'This defines the SAML attribute that should be used for the email address.',
        'label': 'SAML Email Attribute',
        'stype': str,
        'default': 'email',
    }))

    inst.set(SettingMap.SAML_ATTRIBUTE_GIVENNAME, Setting(**{
        'name': SettingMap.SAML_ATTRIBUTE_GIVENNAME,
        'description': 'This defines the SAML attribute that should be used for the first / given name.',
        'label': 'SAML First / Given Name Attribute',
        'stype': str,
        'default': 'givenname',
    }))

    inst.set(SettingMap.SAML_ATTRIBUTE_GROUP, Setting(**{
        'name': SettingMap.SAML_ATTRIBUTE_GROUP,
        'description': 'This defines the SAML attribute that should be used for the group membership.',
        'label': 'SAML Group Attribute',
        'stype': str,
        'default': None,
    }))

    inst.set(SettingMap.SAML_ATTRIBUTE_NAME, Setting(**{
        'name': SettingMap.SAML_ATTRIBUTE_NAME,
        'description': 'This defines the SAML attribute that should be used to populate both the first / given and '
                       'last / surname fields by splitting on the first space.',
        'label': 'SAML Full Name Attribute',
        'stype': str,
        'default': None,
    }))

    inst.set(SettingMap.SAML_ATTRIBUTE_SURNAME, Setting(**{
        'name': SettingMap.SAML_ATTRIBUTE_SURNAME,
        'description': 'This defines the SAML attribute that should be used for the last / surname.',
        'label': 'SAML Last / Surname Attribute',
        'stype': str,
        'default': 'surname',
    }))

    inst.set(SettingMap.SAML_ATTRIBUTE_USERNAME, Setting(**{
        'name': SettingMap.SAML_ATTRIBUTE_USERNAME,
        'description': 'This defines the SAML attribute that should be used for the username.',
        'label': 'SAML Username Attribute',
        'stype': str,
        'default': None,
    }))

    inst.set(SettingMap.SAML_CERT, Setting(**{
        'name': SettingMap.SAML_CERT,
        'description': 'This defines the SAML certificate used for signing and encryption.',
        'label': 'SAML Certificate',
        'stype': str,
        'default': None,
    }))

    inst.set(SettingMap.SAML_DEBUG, Setting(**{
        'name': SettingMap.SAML_DEBUG,
        'description': 'This determines whether SAML debugging should be enabled.',
        'label': 'SAML Debug',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.SAML_ENABLED, Setting(**{
        'name': SettingMap.SAML_ENABLED,
        'description': 'This determines whether SAML authentication should be enabled.',
        'label': 'SAML Enabled',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.SAML_GROUP_ADMIN_NAME, Setting(**{
        'name': SettingMap.SAML_GROUP_ADMIN_NAME,
        'description': 'This defines the SAML group name that should be used for the admin flag.',
        'label': 'SAML Admin Group',
        'stype': str,
        'default': None,
    }))

    inst.set(SettingMap.SAML_GROUP_OPERATOR_NAME, Setting(**{
        'name': SettingMap.SAML_GROUP_OPERATOR_NAME,
        'description': 'This defines the SAML group name that should be used for the operator flag.',
        'label': 'SAML Operator Group',
        'stype': str,
        'default': None,
    }))

    inst.set(SettingMap.SAML_GROUP_TO_ACCOUNT_MAPPING, Setting(**{
        'name': SettingMap.SAML_GROUP_TO_ACCOUNT_MAPPING,
        'description': 'This defines the SAML group to PDA account mapping in the format of "{GROUP}={ACCOUNT_NAME},'
                       '{GROUP}={ACCOUNT_NAME}".',
        'label': 'SAML Group to Account Mapping',
        'stype': str,
        'default': None,
    }))

    inst.set(SettingMap.SAML_IDP_ENTITY_ID, Setting(**{
        'name': SettingMap.SAML_IDP_ENTITY_ID,
        'description': 'This defines the SAML Identity Provider entity ID.',
        'label': 'SAML Identity Provider Entity ID',
        'stype': str,
        'default': None,
    }))

    inst.set(SettingMap.SAML_IDP_SSO_BINDING, Setting(**{
        'name': SettingMap.SAML_IDP_SSO_BINDING,
        'description': 'This defines the SAML Identity Provider single sign-on binding.',
        'label': 'SAML Identity Provider Single Sign-On Binding',
        'stype': str,
        'default': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
    }))

    inst.set(SettingMap.SAML_KEY, Setting(**{
        'name': SettingMap.SAML_KEY,
        'description': 'This defines the SAML key used for signing and encryption.',
        'label': 'SAML Key',
        'stype': str,
        'default': None,
    }))

    inst.set(SettingMap.SAML_LOGOUT, Setting(**{
        'name': SettingMap.SAML_LOGOUT,
        'description': 'This determines whether a SAML logout should be performed in the logout app action.',
        'label': 'SAML Logout',
        'stype': bool,
        'default': True,
    }))

    inst.set(SettingMap.SAML_LOGOUT_URL, Setting(**{
        'name': SettingMap.SAML_LOGOUT_URL,
        'description': 'This defines the SAML logout URL.',
        'label': 'SAML Logout URL',
        'stype': str,
        'default': None,
    }))

    inst.set(SettingMap.SAML_METADATA_CACHE_LIFETIME, Setting(**{
        'name': SettingMap.SAML_METADATA_CACHE_LIFETIME,
        'description': 'This defines the SAML metadata cache lifetime in seconds.',
        'label': 'SAML Metadata Cache Lifetime',
        'stype': int,
        'default': 1,
    }))

    inst.set(SettingMap.SAML_METADATA_URL, Setting(**{
        'name': SettingMap.SAML_METADATA_URL,
        'description': 'This defines the SAML metadata URL.',
        'label': 'SAML Metadata URL',
        'stype': str,
        'default': None,
    }))

    inst.set(SettingMap.SAML_NAMEID_FORMAT, Setting(**{
        'name': SettingMap.SAML_NAMEID_FORMAT,
        'description': 'This defines the SAML name ID format.',
        'label': 'SAML Name ID Format',
        'stype': str,
        'default': None,
    }))

    inst.set(SettingMap.SAML_PATH, Setting(**{
        'name': SettingMap.SAML_PATH,
        'description': 'This defines the SAML path in the file system with either an absolute path or a path relative '
                       'to the application root.',
        'label': 'SAML File System Path',
        'stype': str,
        'default': './saml',
    }))

    inst.set(SettingMap.SAML_SIGN_REQUEST, Setting(**{
        'name': SettingMap.SAML_SIGN_REQUEST,
        'description': 'This determines whether a SAML request should be signed.',
        'label': 'SAML Request Signing',
        'stype': bool,
        'default': True,
    }))

    inst.set(SettingMap.SAML_SP_CONTACT_MAIL, Setting(**{
        'name': SettingMap.SAML_SP_CONTACT_MAIL,
        'description': 'This defines the SAML service provider contact email address.',
        'label': 'SAML Service Provider Contact Email',
        'stype': str,
        'default': None,
    }))

    inst.set(SettingMap.SAML_SP_CONTACT_NAME, Setting(**{
        'name': SettingMap.SAML_SP_CONTACT_NAME,
        'description': 'This defines the SAML service provider contact name.',
        'label': 'SAML Service Provider Contact Name',
        'stype': str,
        'default': None,
    }))

    inst.set(SettingMap.SAML_SP_ENTITY_ID, Setting(**{
        'name': SettingMap.SAML_SP_ENTITY_ID,
        'description': 'This defines the SAML service provider entity ID.',
        'label': 'SAML Service Provider Entity ID',
        'stype': str,
        'default': None,
    }))

    inst.set(SettingMap.SAML_WANT_MESSAGE_SIGNED, Setting(**{
        'name': SettingMap.SAML_WANT_MESSAGE_SIGNED,
        'description': 'This determines whether a SAML message should be signed.',
        'label': 'SAML Message Signing',
        'stype': bool,
        'default': True,
    }))

    inst.set(SettingMap.SECRET_KEY, Setting(**{
        'name': SettingMap.SECRET_KEY,
        'description': 'This defines the secret key used for session signing.',
        'label': 'Secret Key',
        'stype': str,
        'default': 'e951e5a1f4b94151b360f47edf596dd2',
    }))

    inst.set(SettingMap.SERVER_EXTERNAL_SSL, Setting(**{
        'name': SettingMap.SERVER_EXTERNAL_SSL,
        'description': 'This determines whether the server is externally SSL terminated.',
        'label': 'Server External SSL',
        'stype': bool,
        'default': True,
    }))

    inst.set(SettingMap.SESSION_COOKIE_SECURE, Setting(**{
        'name': SettingMap.SESSION_COOKIE_SECURE,
        'description': 'This determines whether the session cookie should be secure.',
        'label': 'Session Cookie Secure',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.SESSION_TIMEOUT, Setting(**{
        'name': SettingMap.SESSION_TIMEOUT,
        'description': 'This defines the session timeout in minutes.',
        'label': 'Session Timeout',
        'stype': int,
        'default': 10,
    }))

    inst.set(SettingMap.SESSION_TYPE, Setting(**{
        'name': SettingMap.SESSION_TYPE,
        'description': 'This defines the session storage type.',
        'label': 'Session Storage Type',
        'stype': str,
        'default': 'sqlalchemy',
    }))

    inst.set(SettingMap.SIGNUP_ENABLED, Setting(**{
        'name': SettingMap.SIGNUP_ENABLED,
        'description': 'This determines whether open user registration is enabled.',
        'label': 'Open User Registration',
        'stype': bool,
        'default': True,
    }))

    inst.set(SettingMap.SITE_NAME, Setting(**{
        'name': SettingMap.SITE_NAME,
        'description': 'This defines the site name used through-out the app.',
        'label': 'Site Name',
        'stype': str,
        'default': 'PowerDNS-Admin',
    }))

    inst.set(SettingMap.SITE_URL, Setting(**{
        'name': SettingMap.SITE_URL,
        'description': 'This defines the site URL used through-out the app.',
        'label': 'Site URL',
        'stype': str,
        'default': 'http://localhost:9191',
    }))

    inst.set(SettingMap.SQLALCHEMY_DATABASE_URI, Setting(**{
        'name': SettingMap.SQLALCHEMY_DATABASE_URI,
        'description': 'This defines the SQLAlchemy database URI.',
        'label': 'SQLAlchemy Database URI',
        'stype': str,
        'default': 'sqlite:///' + os.path.join(basedir, 'pdns.db'),
    }))

    inst.set(SettingMap.SQLALCHEMY_ENGINE_OPTIONS, Setting(**{
        'name': SettingMap.SQLALCHEMY_ENGINE_OPTIONS,
        'description': 'This defines the SQLAlchemy engine options.',
        'label': 'SQLAlchemy Engine Options',
        'stype': dict,
        'default': {},
    }))

    inst.set(SettingMap.SQLALCHEMY_TRACK_MODIFICATIONS, Setting(**{
        'name': SettingMap.SQLALCHEMY_TRACK_MODIFICATIONS,
        'description': 'This determines whether SQLAlchemy should track modifications.',
        'label': 'SQLAlchemy Track Modifications',
        'stype': bool,
        'default': True,
    }))

    inst.set(SettingMap.TTL_OPTIONS, Setting(**{
        'name': SettingMap.TTL_OPTIONS,
        'description': 'This defines the TTL options available to the user.',
        'label': 'TTL Options',
        'stype': str,
        'default': '1 minute,5 minutes,30 minutes,60 minutes,24 hours',
    }))

    inst.set(SettingMap.URN_VALUE, Setting(**{
        'name': SettingMap.URN_VALUE,
        'description': 'This defines the URN prefix used for LDAP role auto-provisioning.',
        'label': 'LDAP Role Auto-Provisioning URN Prefix',
        'stype': str,
        'default': '',
    }))

    inst.set(SettingMap.VERIFY_SSL_CONNECTIONS, Setting(**{
        'name': SettingMap.VERIFY_SSL_CONNECTIONS,
        'description': 'This determines whether SSL connections should be verified.',
        'label': 'SSL Connection Verification',
        'stype': bool,
        'default': True,
    }))

    inst.set(SettingMap.VERIFY_USER_EMAIL, Setting(**{
        'name': SettingMap.VERIFY_USER_EMAIL,
        'description': 'This determines whether user email addresses should be verified.',
        'label': 'User Email Verification',
        'stype': bool,
        'default': False,
    }))

    inst.set(SettingMap.WARN_SESSION_TIMEOUT, Setting(**{
        'name': SettingMap.WARN_SESSION_TIMEOUT,
        'description': 'This determines whether to show a session timeout warning to the user.',
        'label': 'Session Timeout Warning',
        'stype': bool,
        'default': True,
    }))

    initialized = True
