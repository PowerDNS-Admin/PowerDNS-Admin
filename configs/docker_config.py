import os

PORT = 80
SQLALCHEMY_DATABASE_URI = os.getenv(
    'SQLALCHEMY_DATABASE_URI',
    'sqlite:////data/powerdns-admin.db'
)

CAPTCHA_ENABLE = False
