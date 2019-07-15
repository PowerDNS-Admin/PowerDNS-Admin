# defaults for Docker image
BIND_ADDRESS='0.0.0.0'
PORT=80

legal_envvars = (
    'SECRET_KEY',
    'BIND_ADDRESS',
    'PORT',
    'TIMEOUT',
    'LOG_LEVEL',
    'LOG_FILE',
    'SALT',
    'UPLOAD_DIR',
    'SQLALCHEMY_TRACK_MODIFICATIONS',
    'SQLALCHEMY_DATABASE_URI',
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
)

legal_envvars_int = (
    'PORT',
    'TIMEOUT',
    'SAML_METADATA_CACHE_LIFETIME',
)

legal_envvars_bool = (
    'SQLALCHEMY_TRACK_MODIFICATIONS',
    'SAML_ENABLED',
    'SAML_DEBUG',
    'SAML_SIGN_REQUEST',
    'SAML_WANT_MESSAGE_SIGNED',
    'SAML_LOGOUT',
)

# import everything from environment variables
import os
import sys
for v in legal_envvars:
    if v in os.environ:
        ret = os.environ[v]
        if v in legal_envvars_bool:
            ret = bool(ret)
        if v in legal_envvars_int:
            ret = int(ret)
        sys.modules[__name__].__dict__[v] = ret


