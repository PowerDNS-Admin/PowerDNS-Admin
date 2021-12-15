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

# SAML Authnetication
SAML_ENABLED = False
# SAML_DEBUG = True
# SAML_PATH = os.path.join(os.path.dirname(__file__), 'saml')
# ##Example for ADFS Metadata-URL
# SAML_METADATA_URL = 'https://<hostname>/FederationMetadata/2007-06/FederationMetadata.xml'
# #Cache Lifetime in Seconds
# SAML_METADATA_CACHE_LIFETIME = 1

# # SAML SSO binding format to use
# ## Default: library default (urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect)
# #SAML_IDP_SSO_BINDING = 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'

# ## EntityID of the IdP to use. Only needed if more than one IdP is
# ##   in the SAML_METADATA_URL
# ### Default: First (only) IdP in the SAML_METADATA_URL
# ### Example: https://idp.example.edu/idp
# #SAML_IDP_ENTITY_ID = 'https://idp.example.edu/idp'
# ## NameID format to request
# ### Default: The SAML NameID Format in the metadata if present,
# ###   otherwise urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified
# ### Example: urn:oid:0.9.2342.19200300.100.1.1
# #SAML_NAMEID_FORMAT = 'urn:oid:0.9.2342.19200300.100.1.1'

# Following parameter defines RequestedAttributes section in SAML metadata
# since certain iDPs require explicit attribute request. If not provided section
# will not be available in metadata.
#
# Possible attributes:
# name (mandatory), nameFormat, isRequired, friendlyName
#
# NOTE: This parameter requires to be entered in valid JSON format as displayed below
# and multiple attributes can given
#
# Following example:
#
# SAML_SP_REQUESTED_ATTRIBUTES = '[ \
# {"name": "urn:oid:0.9.2342.19200300.100.1.3", "nameFormat": "urn:oasis:names:tc:SAML:2.0:attrname-format:uri", "isRequired": true, "friendlyName": "email"}, \
# {"name": "mail", "isRequired": false, "friendlyName": "test-field"} \
# ]'
#
# produces following metadata section:
# <md:AttributeConsumingService index="1">
# <md:RequestedAttribute Name="urn:oid:0.9.2342.19200300.100.1.3" NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:uri" FriendlyName="email" isRequired="true"/>
# <md:RequestedAttribute Name="mail" FriendlyName="test-field"/>
# </md:AttributeConsumingService>


# ## Attribute to use for Email address
# ### Default: email
# ### Example: urn:oid:0.9.2342.19200300.100.1.3
# #SAML_ATTRIBUTE_EMAIL = 'urn:oid:0.9.2342.19200300.100.1.3'

# ## Attribute to use for Given name
# ### Default: givenname
# ### Example: urn:oid:2.5.4.42
# #SAML_ATTRIBUTE_GIVENNAME = 'urn:oid:2.5.4.42'

# ## Attribute to use for Surname
# ### Default: surname
# ### Example: urn:oid:2.5.4.4
# #SAML_ATTRIBUTE_SURNAME = 'urn:oid:2.5.4.4'

# ## Attribute to use for username
# ### Default: Use NameID instead
# ### Example: urn:oid:0.9.2342.19200300.100.1.1
# #SAML_ATTRIBUTE_USERNAME = 'urn:oid:0.9.2342.19200300.100.1.1'

# ## Attribute to get admin status from
# ### Default: Don't control admin with SAML attribute
# ### Example: https://example.edu/pdns-admin
# ### If set, look for the value 'true' to set a user as an administrator
# ### If not included in assertion, or set to something other than 'true',
# ###  the user is set as a non-administrator user.
# #SAML_ATTRIBUTE_ADMIN = 'https://example.edu/pdns-admin'

# ## Attribute to get account names from
# ### Default: Don't control accounts with SAML attribute
# ### If set, the user will be added and removed from accounts to match
# ###  what's in the login assertion. Accounts that don't exist will
# ###  be created and the user added to them.
# SAML_ATTRIBUTE_ACCOUNT = 'https://example.edu/pdns-account'

# SAML_SP_ENTITY_ID = 'http://<SAML SP Entity ID>'
# SAML_SP_CONTACT_NAME = '<contact name>'
# SAML_SP_CONTACT_MAIL = '<contact mail>'

# Configures the path to certificate file and it's respective private key file
# This pair is used for signing metadata, encrypting tokens and all other signing/encryption
# tasks during communication between iDP and SP
# NOTE: if this two parameters aren't explicitly provided, self-signed certificate-key pair
# will be generated in "PowerDNS-Admin" root directory
# ###########################################################################################
# CAUTION: For production use, usage of self-signed certificates it's highly discouraged.
# Use certificates from trusted CA instead
# ###########################################################################################
# SAML_CERT_FILE = '/etc/pki/powerdns-admin/cert.crt'
# SAML_CERT_KEY = '/etc/pki/powerdns-admin/key.pem'

# Configures if SAML tokens should be encrypted.
# SAML_SIGN_REQUEST = False
# #Use SAML standard logout mechanism retreived from idp metadata
# #If configured false don't care about SAML session on logout.
# #Logout from PowerDNS-Admin only and keep SAML session authenticated.
# SAML_LOGOUT = False
# #Configure to redirect to a different url then PowerDNS-Admin login after SAML logout
# #for example redirect to google.com after successful saml logout
# #SAML_LOGOUT_URL = 'https://google.com'

# #SAML_ASSERTION_ENCRYPTED = True
# SAML_WANT_MESSAGE_SIGNED

# SAML Autoprovisioning
# If toggled on, the PDA Role and the associations of users found in the local db
# will be directly updated from the SAML IDP every time they log in.
# NOTE: This feature and the assertion of "Admin / Account" attributes are mutually exclusive.
# If used, the values for Admin/Account given above will be ignored.
SAML_AUTOPROVISIONING = True
# The urn value of the attribute in the SAML Authn Response where PDA will look
# for a new Role and/or new associations to domains/accounts.
# Example: urn:oid:1.3.6.1.4.1.5923.1.1.1.7
# The record syntax for this attribute inside the SAML Response must look like:
# prefix:powerdns-admin:PDA-Role, to provision an Administrator or Operator, or
# prefix:powerdns-admin:User:<domain>:<account>, provision a User
# who has access to one or more Domains and belongs to one or more Accounts.
# the "prefix" is given in the next attribute
SAML_AUTOPROVISIONING_ATTRIBUTE = 'urn:oid:1.3.6.1.4.1.5923.1.1.1.7'
# The prefix used before the static keyword "powerdns-admin" for your entitlements
# in the SAML Response. Must be a valid URN.
# Example: urn:mace:example.com
SAML_URN_PREFIX = 'urn:mace:example.com'
# If toggled on, SAML logins that have no valid "powerdns-admin" records
# to their autoprovisioning field, will lose all their associations
# with any domain or account, also reverting to a User in the process,
# despite their current role in the local db.
# If toggled off, in the same scenario they get to keep
# their existing associations and their current Role.
### CAUTION: Enabling this feature will revoke existing users' access to their
# associated domains unless they have their autoprovisioning field prepopulated.
SAML_PURGE = False


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
