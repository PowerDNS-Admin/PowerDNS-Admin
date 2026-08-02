import os

PORT = 80
SQLALCHEMY_DATABASE_URI = os.getenv(
    'SQLALCHEMY_DATABASE_URI',
    'mysql://powerdns_admin:changeme@mysql/powerdns_admin'
)

CAPTCHA_ENABLE = False