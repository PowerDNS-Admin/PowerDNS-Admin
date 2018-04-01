import os
basedir = os.path.abspath(os.path.dirname(__file__))

# BASIC APP CONFIG
WTF_CSRF_ENABLED = True
SECRET_KEY = 'changeme'
LOG_LEVEL = 'DEBUG'
LOG_FILE = 'log.txt'

# TIMEOUT - for large zones
TIMEOUT = 10

# UPLOAD DIR
UPLOAD_DIR = os.path.join(basedir, 'upload')

# DATABASE CONFIG FOR MYSQL
DB_USER = 'powerdnsadmin'
DB_PASSWORD = 'powerdnsadminpassword'
DB_HOST = 'docker.for.mac.localhost'
DB_NAME = 'powerdnsadmin'

#MySQL
SQLALCHEMY_DATABASE_URI = 'mysql://'+DB_USER+':'+DB_PASSWORD+'@'+DB_HOST+'/'+DB_NAME
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = True

# AUTHENTICATION CONFIG
BASIC_ENABLED = True
SIGNUP_ENABLED = True


# LDAP CONFIG
LDAP_ENABLE = False
LDAP_TYPE = 'ldap'
LDAP_URI = 'ldaps://your-ldap-server:636'
# with LDAP_BIND_TYPE you can specify 'direct' or 'search' to use user credentials
# for binding or a predefined LDAP_USERNAME and LDAP_PASSWORD, binding with non-DN only works with AD
LDAP_BIND_TYPE= 'direct' # direct or search
LDAP_USERNAME = 'cn=dnsuser,ou=users,ou=services,dc=duykhanh,dc=me'
LDAP_PASSWORD = 'dnsuser'
LDAP_SEARCH_BASE = 'ou=System Admins,ou=People,dc=duykhanh,dc=me'
# Additional options only if LDAP_TYPE=ldap
LDAP_USERNAMEFIELD = 'uid'
LDAP_FILTER = '(objectClass=inetorgperson)'
# enable LDAP_GROUP_SECURITY to allow Admin and User roles based on LDAP groups
#LDAP_GROUP_SECURITY = True # True or False
#LDAP_ADMIN_GROUP = 'CN=DnsAdmins,CN=Users,DC=example,DC=me'
#LDAP_USER_GROUP = 'CN=Domain Admins,CN=Users,DC=example,DC=me'

## AD CONFIG
#LDAP_TYPE = 'ad'
#LDAP_URI = 'ldaps://your-ad-server:636'
#LDAP_USERNAME = 'cn=dnsuser,ou=Users,dc=domain,dc=local'
#LDAP_PASSWORD = 'dnsuser'
#LDAP_SEARCH_BASE = 'dc=domain,dc=local'
## You may prefer 'userPrincipalName' instead
#LDAP_USERNAMEFIELD = 'sAMAccountName'
## AD Group that you would like to have accesss to web app
#LDAP_FILTER = 'memberof=cn=DNS_users,ou=Groups,dc=domain,dc=local'


## GITHUB AUTHENTICATION
GITHUB_OAUTH_ENABLE = False
GITHUB_OAUTH_KEY = ''
GITHUB_OAUTH_SECRET = ''
GITHUB_OAUTH_SCOPE = 'email'
GITHUB_OAUTH_URL = 'http://127.0.0.1:9191/api/v3/'
GITHUB_OAUTH_TOKEN = 'http://127.0.0.1:9191/oauth/token'
GITHUB_OAUTH_AUTHORIZE = 'http://127.0.0.1:9191/oauth/authorize'


# GOOGLE AUTHENTICATION
GOOGLE_OAUTH_ENABLE = False
GOOGLE_OAUTH_CLIENT_ID = ''
GOOGLE_OAUTH_CLIENT_SECRET = ''
GOOGLE_REDIRECT_URI = '/user/authorized'
GOOGLE_TOKEN_URL = 'https://accounts.google.com/o/oauth2/token'
GOOGLE_TOKEN_PARAMS = {
    'scope': 'email profile'
}
GOOGLE_AUTHORIZE_URL='https://accounts.google.com/o/oauth2/auth'
GOOGLE_BASE_URL='https://www.googleapis.com/oauth2/v1/'


# POWERDNS CONFIG
PDNS_STATS_URL = 'http://192.168.100.100:8081/'
PDNS_API_KEY = 'changeme'
PDNS_VERSION = '4.1.1'

# RECORDS ALLOWED TO EDIT
RECORDS_ALLOW_EDIT = ['A', 'AAAA', 'CAA', 'CNAME', 'MX', 'PTR', 'SPF', 'SRV', 'TXT', 'NS']

# RECORDS ALLOWED TO EDIT FOR REVERSE DOMAINS
REVERSE_ALLOW_EDIT = ['PTR', 'NS']

# EXPERIMENTAL FEATURES
PRETTY_IPV6_PTR = False
