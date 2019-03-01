import pytest
import sys
import flask_migrate
import os
from base64 import b64encode
from unittest import mock
sys.path.append(os.getcwd())

from app.models import Role, User, Setting, ApiKey, Domain
from app import app, db
from app.blueprints.api import api_blueprint
from app.lib.log import logging


@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()

    yield client

def load_data(setting_name, *args, **kwargs):
    if setting_name == 'maintenance':
        return 0
    if setting_name == 'pdns_api_url':
        return 'http://empty'
    if setting_name == 'pdns_api_key':
        return 'XXXX'
    if setting_name == 'pdns_version':
        return '4.1.0'
    if setting_name == 'google_oauth_enabled':
        return False
    if setting_name == 'session_timeout':
        return 10
    if setting_name == 'allow_user_create_domain':
        return True

@pytest.fixture
def basic_auth_admin_headers():
    test_admin_user = app.config.get('TEST_ADMIN_USER')
    test_admin_pass = app.config.get('TEST_ADMIN_PASSWORD')
    user_pass = "{0}:{1}".format(test_admin_user, test_admin_pass)
    user_pass_base64 = b64encode(user_pass.encode('utf-8'))
    headers = {
        "Authorization": "Basic {0}".format(user_pass_base64.decode('utf-8'))
    }
    return headers


@pytest.fixture
def basic_auth_user_headers():
    test_user = app.config.get('TEST_USER')
    test_user_pass = app.config.get('TEST_USER_PASSWORD')
    user_pass = "{0}:{1}".format(test_user, test_user_pass)
    user_pass_base64 = b64encode(user_pass.encode('utf-8'))
    headers = {
        "Authorization": "Basic {0}".format(user_pass_base64.decode('utf-8'))
    }
    return headers


@pytest.fixture(scope="module")
def initial_data():
    pdns_proto = os.environ['PDNS_PROTO']
    pdns_host = os.environ['PDNS_HOST']
    pdns_port = os.environ['PDNS_PORT']
    pdns_api_url = '{0}://{1}:{2}'.format(pdns_proto, pdns_host, pdns_port)

    api_url_setting = Setting('pdns_api_url', pdns_api_url)
    api_key_setting = Setting('pdns_api_key', os.environ['PDNS_API_KEY'])
    allow_create_domain_setting = Setting('allow_user_create_domain', True)

    try:
        with app.app_context():
            flask_migrate.upgrade()

        db.session.add(api_url_setting)
        db.session.add(api_key_setting)
        db.session.add(allow_create_domain_setting)

        test_user_pass = app.config.get('TEST_USER_PASSWORD')
        test_user = app.config.get('TEST_USER')
        test_admin_user = app.config.get('TEST_ADMIN_USER')
        test_admin_pass = app.config.get('TEST_ADMIN_PASSWORD')

        admin_user = User(
                            username=test_admin_user,
                            plain_text_password=test_admin_pass,
                            email="admin@admin.com"
                        )
        msg = admin_user.create_local_user()

        if not msg:
            raise Exception("Error occured creating user {0}".format(msg))

        ordinary_user = User(
                                username=test_user,
                                plain_text_password=test_user_pass,
                                email="test@test.com"
                            )
        msg = ordinary_user.create_local_user()

        if not msg:
            raise Exception("Error occured creating user {0}".format(msg))

    except Exception as e:
        logging.error("Unexpected ERROR: {0}".format(e))
        raise e

    yield

    db.session.close()
    os.unlink(app.config['TEST_DB_LOCATION'])


@pytest.fixture(scope="module")
def initial_apikey_data():
    pdns_proto = os.environ['PDNS_PROTO']
    pdns_host = os.environ['PDNS_HOST']
    pdns_port = os.environ['PDNS_PORT']
    pdns_api_url = '{0}://{1}:{2}'.format(pdns_proto, pdns_host, pdns_port)

    api_url_setting = Setting('pdns_api_url', pdns_api_url)
    api_key_setting = Setting('pdns_api_key', os.environ['PDNS_API_KEY'])
    allow_create_domain_setting = Setting('allow_user_create_domain', True)

    try:
        with app.app_context():
            flask_migrate.upgrade()

        db.session.add(api_url_setting)
        db.session.add(api_key_setting)
        db.session.add(allow_create_domain_setting)

        test_user_apikey = app.config.get('TEST_USER_APIKEY')
        test_admin_apikey = app.config.get('TEST_ADMIN_APIKEY')

        dummy_apikey = ApiKey(
            desc="dummy",
            role_name="Administrator"
        )

        admin_key = dummy_apikey.get_hashed_password(
            plain_text_password=test_admin_apikey
        ).decode('utf-8')

        admin_apikey = ApiKey(
            key=admin_key,
            desc="test admin apikey",
            role_name="Administrator"
        )
        admin_apikey.create()

        user_key = dummy_apikey.get_hashed_password(
            plain_text_password=test_user_apikey
        ).decode('utf-8')

        user_apikey = ApiKey(
            key=user_key,
            desc="test user apikey",
            role_name="User"
        )
        user_apikey.create()

    except Exception as e:
        logging.error("Unexpected ERROR: {0}".format(e))
        raise e

    yield

    db.session.close()
    os.unlink(app.config['TEST_DB_LOCATION'])


@pytest.fixture
def zone_data():
    data = {
        "name": "example.org.",
        "kind": "NATIVE",
        "nameservers": ["ns1.example.org."]
    }
    return data


@pytest.fixture
def created_zone_data():
    data = {
      'url': '/api/v1/servers/localhost/zones/example.org.',
      'soa_edit_api': 'DEFAULT',
      'last_check': 0,
      'masters': [],
      'dnssec': False,
      'notified_serial': 0,
      'nsec3narrow': False,
      'serial': 2019013101,
      'nsec3param': '',
      'soa_edit': '',
      'api_rectify': False,
      'kind': 'Native',
      'rrsets': [
        {
          'comments': [],
          'type': 'SOA',
          'name': 'example.org.',
          'ttl': 3600,
          'records': [
            {
              'content': 'a.misconfigured.powerdns.server. hostmaster.example.org. 2019013101 10800 3600 604800 3600',
              'disabled': False
            }
          ]
        },
        {
          'comments': [],
          'type': 'NS',
          'name': 'example.org.',
          'ttl': 3600,
          'records': [
            {
              'content': 'ns1.example.org.',
              'disabled': False
            }
          ]
        }
      ],
      'name': 'example.org.',
      'account': '',
      'id': 'example.org.'
    }
    return data


def user_apikey_data():
    data = {
        "description": "userkey",
        "domains": [
            "example.org"
        ],
        "role": "User"
    }
    return data


def admin_apikey_data():
    data = {
        "description": "masterkey",
        "domains": [],
        "role": "Administrator"
    }
    return data


@pytest.fixture(scope='module')
def user_apikey_integration():
    test_user_apikey = app.config.get('TEST_USER_APIKEY')
    headers = create_apikey_headers(test_user_apikey)
    return headers


@pytest.fixture(scope='module')
def admin_apikey_integration():
    test_user_apikey = app.config.get('TEST_ADMIN_APIKEY')
    headers = create_apikey_headers(test_user_apikey)
    return headers


@pytest.fixture(scope='module')
def user_apikey():
    data = user_apikey_data()
    api_key = ApiKey(
        desc=data['description'],
        role_name=data['role'],
        domains=[]
    )
    headers = create_apikey_headers(api_key.plain_key)
    return headers


@pytest.fixture(scope='module')
def admin_apikey():
    data = admin_apikey_data()
    api_key = ApiKey(
        desc=data['description'],
        role_name=data['role'],
        domains=[]
    )
    headers = create_apikey_headers(api_key.plain_key)
    return headers


def create_apikey_headers(passw):
    user_pass_base64 = b64encode(passw.encode('utf-8'))
    headers = {
        "X-API-KEY": "{0}".format(user_pass_base64.decode('utf-8'))
    }
    return headers
