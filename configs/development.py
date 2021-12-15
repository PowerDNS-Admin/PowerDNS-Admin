import os
#import urllib.parse
basedir = os.path.abspath(os.path.dirname(__file__))

### BASIC APP CONFIG
SALT = '$2b$12$yLUMTIfl21FKJQpTkRQXCu'
SECRET_KEY = 'e951e5a1f4b94151b360f47edf596dd2'
BIND_ADDRESS = '0.0.0.0'
PORT = 9191
OFFLINE_MODE = False

### DATABASE CONFIG
SQLA_DB_USER = 'pda'
SQLA_DB_PASSWORD = 'changeme'
SQLA_DB_HOST = '127.0.0.1'
SQLA_DB_NAME = 'pda'
SQLALCHEMY_TRACK_MODIFICATIONS = True

### DATABASE - MySQL
#SQLALCHEMY_DATABASE_URI = 'mysql://{}:{}@{}/{}'.format(
#    urllib.parse.quote_plus(SQLA_DB_USER),
#    urllib.parse.quote_plus(SQLA_DB_PASSWORD),
#    SQLA_DB_HOST,
#    SQLA_DB_NAME
#)

### DATABASE - SQLite
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'pdns.db')

### SMTP config
# MAIL_SERVER = 'localhost'
# MAIL_PORT = 25
# MAIL_DEBUG = False
# MAIL_USE_TLS = False
# MAIL_USE_SSL = False
# MAIL_USERNAME = None
# MAIL_PASSWORD = None
# MAIL_DEFAULT_SENDER = ('PowerDNS-Admin', 'noreply@domain.ltd')

# Remote authentication settings

# Whether to enable remote user authentication or not
# Defaults to False
# REMOTE_USER_ENABLED=True

# If set, users will be redirected to this location on logout
# Ignore or set to None to avoid redirecting altogether
# Warning: if REMOTE_USER environment variable is still set after logging out and not cleared by
# some external module, not defining a custom logout URL might trigger a loop
# that will just log the user back in right after logging out
# REMOTE_USER_LOGOUT_URL=https://my.sso.com/cas/logout

# An optional list of remote authentication tied cookies to be removed upon logout
# REMOTE_USER_COOKIES=['MOD_AUTH_CAS', 'MOD_AUTH_CAS_S']
