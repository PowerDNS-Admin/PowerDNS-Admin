import os
basedir = os.path.abspath(os.path.dirname(__file__))

# BASIC APP CONFIG
WTF_CSRF_ENABLED = True
SECRET_KEY = 'We are the world'
BIND_ADDRESS = '127.0.0.1'
PORT = 9191
LOGIN_TITLE = "PDNS"

# TIMEOUT - for large zones
TIMEOUT = 10

# LOG CONFIG
LOG_LEVEL = 'DEBUG'
LOG_FILE = 'logfile.log'
# For Docker, leave empty string
#LOG_FILE = ''

# Upload
UPLOAD_DIR = os.path.join(basedir, 'upload')

# DATABASE CONFIG
#You'll need MySQL-python
SQLA_DB_USER = 'powerdnsadmin'
SQLA_DB_PASSWORD = 'powerdnsadminpassword'
SQLA_DB_HOST = 'mysqlhostorip'
SQLA_DB_NAME = 'powerdnsadmin'

#MySQL
#SQLALCHEMY_DATABASE_URI = 'mysql://'+SQLA_DB_USER+':'\
#    +SQLA_DB_PASSWORD+'@'+SQLA_DB_HOST+'/'+SQLA_DB_NAME
#SQLite
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'pdns.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = True

# LDAP CONFIG
LDAP_ENABLED = False
LDAP_TYPE = 'ldap'
LDAP_URI = 'ldaps://your-ldap-server:636'
LDAP_ADMIN_USERNAME = 'cn=admin,dc=mydomain,dc=com'
LDAP_ADMIN_PASSWORD = 'password'
LDAP_SEARCH_BASE = 'dc=mydomain,dc=com'

# Additional options only if LDAP_TYPE=ldap
LDAP_USERNAMEFIELD = 'uid'
LDAP_FILTER = '(objectClass=inetorgperson)'

# enable LDAP_GROUP_SECURITY to allow Admin and User roles based on LDAP groups
LDAP_GROUP_SECURITY = False # True or False
LDAP_ADMIN_GROUP = 'cn=sysops,dc=mydomain,dc=com'
LDAP_USER_GROUP = 'cn=user,dc=mydomain,dc=com'

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

# Github Oauth
GITHUB_OAUTH_ENABLE = False
GITHUB_OAUTH_KEY = ''
GITHUB_OAUTH_SECRET = ''
GITHUB_OAUTH_SCOPE = 'email'
GITHUB_OAUTH_URL = 'http://127.0.0.1:9191/api/v3/'
GITHUB_OAUTH_TOKEN = 'http://127.0.0.1:9191/oauth/token'
GITHUB_OAUTH_AUTHORIZE = 'http://127.0.0.1:9191/oauth/authorize'


# Google OAuth
GOOGLE_OAUTH_ENABLE = False
GOOGLE_OAUTH_CLIENT_ID = ' '
GOOGLE_OAUTH_CLIENT_SECRET = ' '
GOOGLE_REDIRECT_URI = '/user/authorized'
GOOGLE_TOKEN_URL = 'https://accounts.google.com/o/oauth2/token'
GOOGLE_TOKEN_PARAMS = {
    'scope': 'email profile'
}
GOOGLE_AUTHORIZE_URL='https://accounts.google.com/o/oauth2/auth'
GOOGLE_BASE_URL='https://www.googleapis.com/oauth2/v1/'

# SAML Authnetication
SAML_ENABLED = False
SAML_DEBUG = True
SAML_PATH = os.path.join(os.path.dirname(__file__), 'saml')
##Example for ADFS Metadata-URL
SAML_METADATA_URL = 'https://<hostname>/FederationMetadata/2007-06/FederationMetadata.xml'
#Cache Lifetime in Seconds
SAML_METADATA_CACHE_LIFETIME = 1

# SAML SSO binding format to use
## Default: library default (urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect)
#SAML_IDP_SSO_BINDING = 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'

## EntityID of the IdP to use. Only needed if more than one IdP is
##   in the SAML_METADATA_URL
### Default: First (only) IdP in the SAML_METADATA_URL
### Example: https://idp.example.edu/idp
#SAML_IDP_ENTITY_ID = 'https://idp.example.edu/idp'
## NameID format to request
### Default: The SAML NameID Format in the metadata if present,
###   otherwise urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified
### Example: urn:oid:0.9.2342.19200300.100.1.1
#SAML_NAMEID_FORMAT = 'urn:oid:0.9.2342.19200300.100.1.1'

## Attribute to use for Email address
### Default: email
### Example: urn:oid:0.9.2342.19200300.100.1.3
#SAML_ATTRIBUTE_EMAIL = 'urn:oid:0.9.2342.19200300.100.1.3'

## Attribute to use for Given name
### Default: givenname
### Example: urn:oid:2.5.4.42
#SAML_ATTRIBUTE_GIVENNAME = 'urn:oid:2.5.4.42'

## Attribute to use for Surname
### Default: surname
### Example: urn:oid:2.5.4.4
#SAML_ATTRIBUTE_SURNAME = 'urn:oid:2.5.4.4'

## Attribute to use for username
### Default: Use NameID instead
### Example: urn:oid:0.9.2342.19200300.100.1.1
#SAML_ATTRIBUTE_USERNAME = 'urn:oid:0.9.2342.19200300.100.1.1'

## Attribute to get admin status from
### Default: Don't control admin with SAML attribute
### Example: https://example.edu/pdns-admin
### If set, look for the value 'true' to set a user as an administrator
### If not included in assertion, or set to something other than 'true',
###  the user is set as a non-administrator user.
#SAML_ATTRIBUTE_ADMIN = 'https://example.edu/pdns-admin'

## Attribute to get account names from
### Default: Don't control accounts with SAML attribute
### If set, the user will be added and removed from accounts to match
###  what's in the login assertion. Accounts that don't exist will
###  be created and the user added to them.
SAML_ATTRIBUTE_ACCOUNT = 'https://example.edu/pdns-account'

SAML_SP_ENTITY_ID = 'http://<SAML SP Entity ID>'
SAML_SP_CONTACT_NAME = '<contact name>'
SAML_SP_CONTACT_MAIL = '<contact mail>'
#Cofigures if SAML tokens should be encrypted.
#If enabled a new app certificate will be generated on restart
SAML_SIGN_REQUEST = False
#Use SAML standard logout mechanism retreived from idp metadata
#If configured false don't care about SAML session on logout.
#Logout from PowerDNS-Admin only and keep SAML session authenticated.
SAML_LOGOUT = False
#Configure to redirect to a different url then PowerDNS-Admin login after SAML logout
#for example redirect to google.com after successful saml logout
#SAML_LOGOUT_URL = 'https://google.com'

#Default Auth
BASIC_ENABLED = True
SIGNUP_ENABLED = True

# POWERDNS CONFIG
PDNS_STATS_URL = 'http://172.16.214.131:8081/'
PDNS_API_KEY = 'you never know'
PDNS_VERSION = '4.1.1'

# RECORDS ALLOWED TO EDIT
RECORDS_ALLOW_EDIT = ['A', 'AAAA', 'CAA', 'CNAME', 'MX', 'PTR', 'SPF', 'SRV', 'TXT', 'LOC', 'NS', 'PTR', 'SOA']
FORWARD_RECORDS_ALLOW_EDIT = ['A', 'AAAA', 'CAA', 'CNAME', 'MX', 'PTR', 'SPF', 'SRV', 'TXT', 'LOC' 'NS']
REVERSE_RECORDS_ALLOW_EDIT = ['SOA', 'TXT', 'LOC', 'NS', 'PTR']

# ALLOW DNSSEC CHANGES FOR ADMINS ONLY
DNSSEC_ADMINS_ONLY = False

# EXPERIMENTAL FEATURES
PRETTY_IPV6_PTR = False

# Domain updates in background, for big installations
BG_DOMAIN_UPDATES = False
