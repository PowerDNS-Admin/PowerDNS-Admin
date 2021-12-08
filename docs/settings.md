# PowerDNS-Admin Settings

The app has a plethora of settings that may be configured through a number of methods. Unfortunately, at the current state the app does not use a completely uniform naming scheme across configuration methods.

Don't worry though! A strong standard is quickly being implemented with full backwards compatibility so this problem should disappear quickly.

Let's break the application settings keys down into two primary categories, docker only and app settings. Below you will find a detailed description of each setting and how to use it.

## Docker Only Settings

\+ denotes a setting that is planned but not yet implemented.

#### PDA_UID = 1000

This setting controls what user ID is used for various container setup processes during image building. This setting is useful if you're mounting a host path over the /srv/app volume and need to match your host file system permissions.

#### PDA_USER = pda

This setting controls what username is used for various container setup processes during image building. This setting is useful if you're mounting a host path over the /srv/app volume and need to match your host file system permissions.

#### PDA_GID = 1000

This setting controls what group ID is used for various container setup processes during image building. This setting is useful if you're mounting a host path over the /srv/app volume and need to match your host file system permissions.

#### PDA_GROUP = pda

This setting controls what group name is used for various container setup processes during image building. This setting is useful if you're mounting a host path over the /srv/app volume and need to match your host file system permissions.

## App Settings
\* denotes a legacy setting key that will be deprecated.

\+ denotes a setting that is planned but not yet implemented.

**!COMPUTED!** denotes a default setting value that is computed dynamically at the time it is set.

#### PDA_BIND_ADDRESS = 0.0.0.0
The container interface IP mask to bind both gunicorn and the built-in web server to.

#### PDA_BIND_PORT = 80
The container port to bind both gunicorn and the built-in web server to.

#### PDA_DEBUG = false
The debug mode setting of the app.

#### PDA_LOAD_ENV_FILES = true
Whether to automatically convert environment variables beginning with PDA_ and ending with _FILE.

#### PDA_AUTOINIT_ENABLED = true
Whether the automatic first-time initialization feature is enabled.

#### PDA_AUTOINIT_FORCE = false
Whether to force execution of the first-time initialization feature.

#### PDA_CHECK_MYSQL_ENABLED = false
Whether to delay container startup until the configured MySQL server is online.

#### PDA_CHECK_MYSQL_FAIL_DELAY = 2
How many seconds to wait after a MySQL connection attempt failure before trying again.

#### PDA_CHECK_MYSQL_SUCCESS_DELAY = 0
How many seconds to wait after a successful MySQL connection attempt before proceeding to the next step.

#### PDA_CHECK_MYSQL_ATTEMPTS = 30
How many MySQL connection attempts should be made before halting container execution.

#### PDA_CHECK_API_ENABLED = false
Whether to delay container startup until the configured PDNS API key passes authorization to the server.

#### PDA_CHECK_API_FAIL_DELAY = 2
How many seconds to wait after an API connection attempt failure before trying again.

#### PDA_CHECK_API_SUCCESS_DELAY = 0
How many seconds to wait after an API successful connection attempt before proceeding to the next step.

#### PDA_CHECK_API_ATTEMPTS = 15
How many API connection attempts should be made before halting container execution.

#### PDA_CHECK_PYTEST_ENABLED = false
Whether to run the app's Python test unit before starting the primary container process.

#### PDA_GUNICORN_ENABLED = false
Whether to enable the use of gunicorn.

#### PDA_GUNICORN_TIMEOUT = 120
The request timeout in seconds for a gunicorn worker.

#### PDA_GUNICORN_WORKERS = 4
The total number of gunicorn worker threads to spawn.

#### PDA_GUNICORN_LOGLEVEL = info
The log output level of the gunicorn process.

#### PDA_GUNICORN_ARGS = !COMPUTED!
The additional gunicorn arguments that will be appended to the startup command when gunicorn is enabled.

#### PDA_PDNS_API_KEY = CHANGE_ME!
The API key for the associated PowerDNS Authoritative server API.

#### PDA_PDNS_API_VERSION = 4.5.2
The API version of the associated PowerDNS Authoritative server API.

#### PDA_PDNS_API_PROTO = http
The HTTP protocol for the associated PowerDNS Authoritative server API.

#### PDA_PDNS_API_HOST = 127.0.0.1
The hostname or IP address of the associated PowerDNS Authoritative server API.

#### PDA_PDNS_API_PORT = 8081
The port of the associated PowerDNS Authoritative server API.

#### + PDA_ADMIN_USER_USERNAME
The username to use for automatic admin account setup on startup.

#### + PDA_ADMIN_USER_PASSWORD
The password to use for automatic admin account setup on startup.

#### * FLASK_ENV = production
The Flask app environment classification.

**!!! NOTICE !!!** - Setting this to development carries implicit behaviors such as automatically setting the FLASK_DEBUG setting to true.

#### * FLASK_DEBUG = false
The Flask app debug mode setting.

**!!! NOTICE !!!** - Enabling debug mode will cause the debugger to run during app initialization.

#### * FLASK_APP = /srv/app/run.py
The Flask Python file that should be treated as the main app file.

#### * FLASK_CONF
The Flask Python config file path that should be loaded during app initialization.

#### * PDNS_ADMIN_LOG_LEVEL = WARNING
The log output level that the app logging mechanism will use.

#### * LOG_LEVEL = ?
TODO: Find out where this is used and what it's default value is

#### * BIND_ADDRESS = 127.0.0.1
Refer to the PDA_BIND_ADDRESS setting documentation.

#### * PORT = 9191
Refer to the PDA_BIND_PORT setting documentation.

#### * DEBUG_MODE = false
Refer to the PDA_DEBUG setting documentation.

#### * SALT = ?
TODO: Find out where this is used and what it's default value is

TODO: Reassign to PDA_ scoped key

#### * SECRET_KEY = ?
This should be set to a long, random string. [[see here for additional information]](https://flask.palletsprojects.com/en/1.1.x/config/#SECRET_KEY)

TODO: Reassign to PDA_ scoped key

#### * SIGNUP_ENABLED = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * HSTS_ENABLED = false
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * OFFLINE_MODE = false
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * FILE_SYSTEM_SESSIONS_ENABLED = false
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * LOCAL_DB_ENABLED = false
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * LDAP_ENABLED = false
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SQLA_DB_USER = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SQLA_DB_PASSWORD = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SQLA_DB_HOST = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SQLA_DB_PORT = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SQLA_DB_NAME = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SQLALCHEMY_DATABASE_URI = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SQLALCHEMY_TRACK_MODIFICATIONS = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * MAIL_SERVER = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * MAIL_PORT = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * MAIL_DEBUG = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * MAIL_USE_TLS = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * MAIL_USE_SSL = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * MAIL_USERNAME = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * MAIL_PASSWORD = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * MAIL_DEFAULT_SENDER = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * REMOTE_USER_LOGOUT_URL = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * REMOTE_USER_COOKIES = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * OIDC_OAUTH_API_URL = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * OIDC_OAUTH_TOKEN_URL = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * OIDC_OAUTH_AUTHORIZE_URL = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_ENABLED = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_DEBUG = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_PATH = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_ASSERTION_ENCRYPTED = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_METADATA_URL = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_METADATA_CACHE_LIFETIME = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_IDP_SSO_BINDING = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_IDP_ENTITY_ID = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_NAMEID_FORMAT = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_ATTRIBUTE_EMAIL = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_ATTRIBUTE_GIVENNAME = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_ATTRIBUTE_SURNAME = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_ATTRIBUTE_NAME = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_ATTRIBUTE_USERNAME = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_ATTRIBUTE_ADMIN = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_ATTRIBUTE_GROUP = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_CERT = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_KEY = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_GROUP_ADMIN_NAME = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_GROUP_TO_ACCOUNT_MAPPING = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_ATTRIBUTE_ACCOUNT = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_SP_ENTITY_ID = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_SP_CONTACT_NAME = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_SP_CONTACT_MAIL = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_SIGN_REQUEST = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_WANT_MESSAGE_SIGNED = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_LOGOUT = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key

#### * SAML_LOGOUT_URL = ?
TODO: Complete the setting description

TODO: Reassign to PDA_ scoped key
