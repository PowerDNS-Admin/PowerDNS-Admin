import os
basedir = os.path.abspath(os.path.dirname(__file__))

# BASIC APP CONFIG
WTF_CSRF_ENABLED = bool(os.getenv('WTF_CSRF_ENABLED', 'True'))
SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24))
BIND_ADDRESS = os.getenv('BIND_ADDRESS', '127.0.0.1')
PORT = int(os.getenv('BIND_PORT', '80'))
LOGIN_TITLE = os.getenv('LISTEN_TITLE', "PDNS")

# TIMEOUT - for large zones
TIMEOUT = int(os.getenv('TIMEOUT', '10'))

WAITFOR_DB = int(os.getenv('WAITFOR_DB', '60'))

# LOG CONFIG
LOG_LEVEL = os.getenv('LOGLEVEL', 'info')
LOG_FILE = os.getenv('LOG_FILE', 'logfile.log')
# For Docker, leave empty string
#LOG_FILE = ''

# Upload
UPLOAD_DIR = os.getenv('UPLOAD_DIR',
                       os.path.join(basedir, 'upload'))

# DATABASE CONFIG

if bool(os.getenv('SQLA_DB_MSSQL', 'False')):
    #You'll need MySQL-python
    SQLA_DB_USER = os.getenv('SQLA_DB_USER', 'powerdnsadmin')
    SQLA_DB_PASSWORD = os.getenv('SQLA_DB_PASSWORD', 'powerdnsadminpassword')
    SQLA_DB_HOST = os.getenv('SQLA_DB_HOST', 'mysqlhostorip')
    SQLA_DB_NAME = os.getenv('SQLA_DB_NAME', 'powerdnsadmin')

    #MySQL
    SQLALCHEMY_DATABASE_URI = 'mysql://'+SQLA_DB_USER+':'\
        +SQLA_DB_PASSWORD+'@'+SQLA_DB_HOST+'/'+SQLA_DB_NAME
else:
    SQLA_DB_NAME = os.getenv('SQLA_DB_NAME', None)

SQLALCHEMY_MIGRATE_REPO = os.getenv('SQLALCHEMY_MIGRATE_REPO',
                                    os.path.join(basedir, 'db_repository'))
SQLALCHEMY_TRACK_MODIFICATIONS = bool(os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS', 'True'))


# LDAP CONFIG
# set LDAP_TYPE = 'ldap'
## AD CONFIG
#LDAP_TYPE = 'ad'
#LDAP_USERNAMEFIELD = 'sAMAccountName'

LDAP_TYPE = os.getenv('LDAP_TYPE', None)
if LDAP_TYPE is not None:
    LDAP_URI = os.getenv('LDAP_URI', 'ldaps://your-ldap-server:636')
    LDAP_USERNAME = os.getenv('LDAP_USERNAME',
                              'cn=user,ou=users,ou=services,dc=duykhanh,dc=me')
    LDAP_PASSWORD = os.getenv('LDAP_PASSWORD', 'dnsuser')
    LDAP_SEARCH_BASE = os.getenv('LDAP_SEARCH_BASE',
                                 'ou=System Admins,ou=People,dc=duykhanh,dc=me')
    # Additional options only if LDAP_TYPE=ldap
    LDAP_USERNAMEFIELD = os.getenv('LDAP_USERNAMEFIELD', 'uid')
    LDAP_FILTER = os.getenv('LDAP_FILTER', '(objectClass=inetorgperson)')

# Github Oauth

GITHUB_OAUTH_ENABLE = bool(os.getenv('GITHUB_OAUTH_ENABLE', 'False'))
if GITHUB_OAUTH_ENABLE:
    GITHUB_OAUTH_KEY = os.getenv('GITHUB_OAUTH_KEY',
                                 'G0j1Q15aRsn36B3aD6nwKLiYbeirrUPU8nDd1wOC')
    GITHUB_OAUTH_SECRET = os.getenv('GITHUB_OAUTH_SECRET',
                                    '0WYrKWePeBDkxlezzhFbDn1PBnCwEa0vCwVFvy'
                                    '6iLtgePlpT7WfUlAa9sZgm')
    GITHUB_OAUTH_SCOPE = os.getenv('GITHUB_OAUTH_SCOPE', 'email')
    GITHUB_OAUTH_URL = os.getenv('GITHUB_OAUTH_URL',
                                  'http://127.0.0.1:5000/api/v3/')
    GITHUB_OAUTH_TOKEN = os.getenv('GITHUB_OAUTH_TOKEN',
                                   'http://127.0.0.1:5000/oauth/token')
    GITHUB_OAUTH_AUTHORIZE = os.getenv('GITHUB_OAUTH_AUTHORIZE',
                                       'http://127.0.0.1:5000/oauth/authorize')

#Default Auth
BASIC_ENABLED = bool(os.getenv('BASIC_ENABLED', 'True'))
SIGNUP_ENABLED = bool(os.getenv('SIGNUP_ENABLED', 'True'))

# POWERDNS CONFIG
PDNS_STATS_URL = os.getenv('PDNS_STATS_URL', 'http://172.16.214.131:8081/')
PDNS_API_KEY = os.getenv('PDNS_API_KEY', 'you never know')
PDNS_VERSION = os.getenv('PDNS_VERSION', '3.4.7')

# RECORDS ALLOWED TO EDIT
RECORDS_ALLOW_EDIT = ['A', 'AAAA', 'CNAME', 'SPF', 'PTR', 'MX', 'TXT']

# EXPERIMENTAL FEATURES
PRETTY_IPV6_PTR = bool(os.getenv('PRETTY_IPV6_PTR', 'False'))
