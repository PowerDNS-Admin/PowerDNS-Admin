# import everything from environment variables
import os
import sys
import json

# Defaults for Docker image
BIND_ADDRESS = '0.0.0.0'
PORT = 80
SERVER_EXTERNAL_SSL = True
SQLALCHEMY_DATABASE_URI = 'sqlite:////data/powerdns-admin.db'
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True
SESSION_TYPE = 'sqlalchemy'

legal_envvars = (
    'SECRET_KEY',
    'OIDC_OAUTH_ENABLED',
    'OIDC_OAUTH_KEY',
    'OIDC_OAUTH_SECRET',
    'OIDC_OAUTH_API_URL',
    'OIDC_OAUTH_TOKEN_URL',
    'OIDC_OAUTH_AUTHORIZE_URL',
    'OIDC_OAUTH_METADATA_URL',
    'OIDC_OAUTH_LOGOUT_URL',
    'OIDC_OAUTH_SCOPE',
    'OIDC_OAUTH_USERNAME',
    'OIDC_OAUTH_FIRSTNAME',
    'OIDC_OAUTH_LAST_NAME',
    'OIDC_OAUTH_EMAIL',
    'BIND_ADDRESS',
    'PORT',
    'SERVER_EXTERNAL_SSL',
    'LOG_LEVEL',
    'SALT',
    'SQLALCHEMY_TRACK_MODIFICATIONS',
    'SQLALCHEMY_DATABASE_URI',
    'SQLALCHEMY_ENGINE_OPTIONS',
    'MAIL_SERVER',
    'MAIL_PORT',
    'MAIL_DEBUG',
    'MAIL_USE_TLS',
    'MAIL_USE_SSL',
    'MAIL_USERNAME',
    'MAIL_PASSWORD',
    'MAIL_DEFAULT_SENDER',
    'SAML_ENABLED',
    'SAML_DEBUG',
    'SAML_PATH',
    'SAML_METADATA_URL',
    'SAML_METADATA_CACHE_LIFETIME',
    'SAML_IDP_SSO_BINDING',
    'SAML_IDP_ENTITY_ID',
    'SAML_NAMEID_FORMAT',
    'SAML_ATTRIBUTE_EMAIL',
    'SAML_ATTRIBUTE_GIVENNAME',
    'SAML_ATTRIBUTE_SURNAME',
    'SAML_ATTRIBUTE_NAME',
    'SAML_ATTRIBUTE_USERNAME',
    'SAML_ATTRIBUTE_ADMIN',
    'SAML_ATTRIBUTE_GROUP',
    'SAML_GROUP_ADMIN_NAME',
    'SAML_GROUP_TO_ACCOUNT_MAPPING',
    'SAML_ATTRIBUTE_ACCOUNT',
    'SAML_SP_ENTITY_ID',
    'SAML_SP_CONTACT_NAME',
    'SAML_SP_CONTACT_MAIL',
    'SAML_SIGN_REQUEST',
    'SAML_WANT_MESSAGE_SIGNED',
    'SAML_LOGOUT',
    'SAML_LOGOUT_URL',
    'SAML_ASSERTION_ENCRYPTED',
    'REMOTE_USER_LOGOUT_URL',
    'REMOTE_USER_COOKIES',
    'SIGNUP_ENABLED',
    'LOCAL_DB_ENABLED',
    'LDAP_ENABLED',
    'SAML_CERT',
    'SAML_KEY',
    'SESSION_TYPE',
    'SESSION_COOKIE_SECURE',
    'CSRF_COOKIE_SECURE',
    'CAPTCHA_ENABLE',
)

legal_envvars_int = ('PORT', 'MAIL_PORT', 'SAML_METADATA_CACHE_LIFETIME')

legal_envvars_bool = (
    'SQLALCHEMY_TRACK_MODIFICATIONS',
    'HSTS_ENABLED',
    'MAIL_DEBUG',
    'MAIL_USE_TLS',
    'MAIL_USE_SSL',
    'OIDC_OAUTH_ENABLED',
    'SAML_ENABLED',
    'SAML_DEBUG',
    'SAML_SIGN_REQUEST',
    'SAML_WANT_MESSAGE_SIGNED',
    'SAML_LOGOUT',
    'SAML_ASSERTION_ENCRYPTED',
    'REMOTE_USER_ENABLED',
    'SIGNUP_ENABLED',
    'LOCAL_DB_ENABLED',
    'LDAP_ENABLED',
    'SESSION_COOKIE_SECURE',
    'CSRF_COOKIE_SECURE',
    'CAPTCHA_ENABLE',
    'SERVER_EXTERNAL_SSL',
)

legal_envvars_dict = (
    'SQLALCHEMY_ENGINE_OPTIONS',
)

def str2bool(v):
    return v.lower() in ("true", "yes", "1")


def dictfromstr(v, ret):
    try:
        return json.loads(ret)
    except Exception as e:
        print('Cannot parse json {} for variable {}'.format(ret, v))
        print(e)
        raise ValueError


for v in legal_envvars:

    ret = None
    # _FILE suffix will allow to read value from file, useful for Docker containers.
    # secrets feature
    if v + '_FILE' in os.environ:
        if v in os.environ:
            raise AttributeError(
                "Both {} and {} are set but are exclusive.".format(
                    v, v + '_FILE'))
        with open(os.environ[v + '_FILE']) as f:
            ret = f.read()
        f.close()

    elif v in os.environ:
        ret = os.environ[v]

    if ret is not None:
        if v in legal_envvars_bool:
            ret = str2bool(ret)
        if v in legal_envvars_int:
            ret = int(ret)
        if v in legal_envvars_dict:
            ret = dictfromstr(v, ret)
        sys.modules[__name__].__dict__[v] = ret
