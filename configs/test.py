import os
basedir = os.path.abspath(os.path.dirname(__file__))

### BASIC APP CONFIG
SALT = '$2b$12$yLUMTIfl21FKJQpTkRQXCu'
SECRET_KEY = 'e951e5a1f4b94151b360f47edf596dd2'
BIND_ADDRESS = '0.0.0.0'
PORT = 9191
HSTS_ENABLED = False

### DATABASE - MySQL 8.4 (same credentials as docker compose test/dev)
# Compose overrides the host to `mysql`; CI/local runners use 127.0.0.1.
SQLALCHEMY_DATABASE_URI = os.getenv(
    'SQLALCHEMY_DATABASE_URI',
    'mysql://powerdns_admin:changeme@127.0.0.1/powerdns_admin'
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SESSION_TYPE = 'sqlalchemy'

# SAML Authnetication
SAML_ENABLED = False

# TEST SAMPLE DATA
TEST_USER = 'test'
TEST_USER_PASSWORD = 'test'
TEST_ADMIN_USER = 'admin'
TEST_ADMIN_PASSWORD = 'admin'
TEST_USER_APIKEY = 'wewdsfewrfsfsdf'
TEST_ADMIN_APIKEY = 'nghnbnhtghrtert'
