import os
basedir = os.path.abspath(os.path.dirname(__file__))

# BASIC APP CONFIG
WTF_CSRF_ENABLED = True
SECRET_KEY = 'We are the world'
BIND_ADDRESS = '0.0.0.0'
PORT = 9393
LOGIN_TITLE = "PDNS"

# TIMEOUT - for large zones
TIMEOUT = 10

# LOG CONFIG
LOG_LEVEL = 'DEBUG'
LOG_FILE = '/dev/stdout'

# Upload
UPLOAD_DIR = os.path.join(basedir, 'upload')

# DATABASE CONFIG
SQLALCHEMY_DATABASE_URI = 'mysql://root:PowerDNSAdminPassword@mysqldb/powerdns-admin'
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = True

# LDAP CONFIG
LDAP_TYPE = 'ldap' # use 'ad' for MS Active Directory
LDAP_URI = 'ldaps://your-ldap-server:636'
LDAP_USERNAME = 'cn=dnsuser,ou=users,ou=services,dc=duykhanh,dc=me'
LDAP_PASSWORD = 'dnsuser'
LDAP_SEARCH_BASE = 'ou=System Admins,ou=People,dc=duykhanh,dc=me'
# Additional options only if LDAP_TYPE=ldap
LDAP_USERNAMEFIELD = 'uid'
LDAP_FILTER = '(objectClass=inetorgperson)'

#Default Auth
BASIC_ENABLED = True
SIGNUP_ENABLED = True

# POWERDNS CONFIG
PDNS_STATS_URL = 'http://powerdns-server:8081'
PDNS_API_KEY = 'PowerDNSAPIKey'
PDNS_VERSION = '4.0.0'

# RECORDS ALLOWED TO EDIT
RECORDS_ALLOW_EDIT = ['A', 'AAAA', 'CNAME', 'SPF', 'PTR', 'MX', 'TXT']
