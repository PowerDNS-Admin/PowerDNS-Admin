import os
basedir = os.path.abspath(os.path.abspath(os.path.dirname(__file__)))

### BASIC APP CONFIG
SALT = '$2b$12$yLUMTIfl21FKJQpTkRQXCu'
SECRET_KEY = 'e951e5a1f4b94151b360f47edf596dd2'
BIND_ADDRESS = '0.0.0.0'
PORT = 9191
HSTS_ENABLED = False

### DATABASE CONFIG
SQLA_DB_USER = 'pda'
SQLA_DB_PASSWORD = 'changeme'
SQLA_DB_HOST = '127.0.0.1'
SQLA_DB_NAME = 'pda'
SQLALCHEMY_TRACK_MODIFICATIONS = True

### DATBASE - MySQL
SQLALCHEMY_DATABASE_URI = 'mysql://'+SQLA_DB_USER+':'+SQLA_DB_PASSWORD+'@'+SQLA_DB_HOST+'/'+SQLA_DB_NAME

### DATABSE - SQLite
# SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'pdns.db')

# SAML Authnetication
SAML_ENABLED = False
