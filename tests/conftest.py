import os
from base64 import b64encode

import pytest
from flask_migrate import upgrade as flask_migrate_upgrade

from powerdnsadmin import create_app
from powerdnsadmin.models.api_key import ApiKey
from powerdnsadmin.models.base import db
from powerdnsadmin.models.setting import Setting
from powerdnsadmin.models.user import User


@pytest.fixture(scope="session")
def app():
    app = create_app('../configs/test.py')
    yield app


@pytest.fixture
def client(app):
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
    if setting_name == 'allow_user_remove_domain':
        return True


@pytest.fixture
def test_admin_user(app):
    return app.config.get('TEST_ADMIN_USER')


@pytest.fixture
def test_user(app):
    return app.config.get('TEST_USER')


@pytest.fixture
def basic_auth_admin_headers(app):
    test_admin_user = app.config.get('TEST_ADMIN_USER')
    test_admin_pass = app.config.get('TEST_ADMIN_PASSWORD')
    user_pass = "{0}:{1}".format(test_admin_user, test_admin_pass)
    user_pass_base64 = b64encode(user_pass.encode('utf-8'))
    headers = {
        "Authorization": "Basic {0}".format(user_pass_base64.decode('utf-8'))
    }
    return headers


@pytest.fixture
def basic_auth_user_headers(app):
    test_user = app.config.get('TEST_USER')
    test_user_pass = app.config.get('TEST_USER_PASSWORD')
    user_pass = "{0}:{1}".format(test_user, test_user_pass)
    user_pass_base64 = b64encode(user_pass.encode('utf-8'))
    headers = {
        "Authorization": "Basic {0}".format(user_pass_base64.decode('utf-8'))
    }
    return headers


@pytest.fixture(scope="module")
def initial_data(app):

    pdns_proto = os.environ['PDNS_PROTO']
    pdns_host = os.environ['PDNS_HOST']
    pdns_port = os.environ['PDNS_PORT']
    pdns_api_url = '{0}://{1}:{2}'.format(pdns_proto, pdns_host, pdns_port)

    api_url_setting = Setting('pdns_api_url', pdns_api_url)
    api_key_setting = Setting('pdns_api_key', os.environ['PDNS_API_KEY'])
    allow_create_domain_setting = Setting('allow_user_create_domain', True)

    with app.app_context():
        try:
            flask_migrate_upgrade(directory="migrations")
            db.session.add(api_url_setting)
            db.session.add(api_key_setting)
            db.session.add(allow_create_domain_setting)

            test_user = app.config.get('TEST_USER')
            test_user_pass = app.config.get('TEST_USER_PASSWORD')
            test_admin_user = app.config.get('TEST_ADMIN_USER')
            test_admin_pass = app.config.get('TEST_ADMIN_PASSWORD')

            admin_user = User(username=test_admin_user,
                              plain_text_password=test_admin_pass,
                              email="admin@admin.com")
            ret = admin_user.create_local_user()

            if not ret['status']:
                raise Exception("Error occurred creating user {0}".format(ret['msg']))

            ordinary_user = User(username=test_user,
                                 plain_text_password=test_user_pass,
                                 email="test@test.com")
            ret = ordinary_user.create_local_user()

            if not ret['status']:
                raise Exception("Error occurred creating user {0}".format(ret['msg']))

        except Exception as e:
            print("Unexpected ERROR: {0}".format(e))
            raise e

    yield
    os.unlink(app.config['TEST_DB_LOCATION'])


@pytest.fixture(scope="module")
def initial_apikey_data(app):
    pdns_proto = os.environ['PDNS_PROTO']
    pdns_host = os.environ['PDNS_HOST']
    pdns_port = os.environ['PDNS_PORT']
    pdns_api_url = '{0}://{1}:{2}'.format(pdns_proto, pdns_host, pdns_port)

    api_url_setting = Setting('pdns_api_url', pdns_api_url)
    api_key_setting = Setting('pdns_api_key', os.environ['PDNS_API_KEY'])
    allow_create_domain_setting = Setting('allow_user_create_domain', True)
    allow_remove_domain_setting = Setting('allow_user_remove_domain', True)

    with app.app_context():
        try:
            flask_migrate_upgrade(directory="migrations")
            db.session.add(api_url_setting)
            db.session.add(api_key_setting)
            db.session.add(allow_create_domain_setting)
            db.session.add(allow_remove_domain_setting)

            test_user_apikey = app.config.get('TEST_USER_APIKEY')
            test_admin_apikey = app.config.get('TEST_ADMIN_APIKEY')

            dummy_apikey = ApiKey(desc="dummy", role_name="Administrator")

            admin_key = dummy_apikey.get_hashed_password(
                plain_text_password=test_admin_apikey).decode('utf-8')

            admin_apikey = ApiKey(key=admin_key,
                                  desc="test admin apikey",
                                  role_name="Administrator")
            admin_apikey.create()

            user_key = dummy_apikey.get_hashed_password(
                plain_text_password=test_user_apikey).decode('utf-8')

            user_apikey = ApiKey(key=user_key,
                                 desc="test user apikey",
                                 role_name="User")
            user_apikey.create()

        except Exception as e:
            print("Unexpected ERROR: {0}".format(e))
            raise e

    yield
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
        'rrsets': [{
            'comments': [],
            'type': 'SOA',
            'name': 'example.org.',
            'ttl': 3600,
            'records': [{
                'content': 'a.misconfigured.powerdns.server. hostmaster.example.org. 2019013101 10800 3600 604800 3600',
                'disabled': False
            }]
        }, {
            'comments': [],
            'type': 'NS',
            'name': 'example.org.',
            'ttl': 3600,
            'records': [{
                'content': 'ns1.example.org.',
                'disabled': False
            }]
        }],
        'name': 'example.org.',
        'account': '',
        'id': 'example.org.'
    }
    return data


def user_data(app):
    test_user = app.config.get('TEST_USER')
    test_user_pass = app.config.get('TEST_USER_PASSWORD')
    data = {
        "username": test_user,
        "plain_text_password": test_user_pass,
        "email": "test@test.com"
    }
    return data


def user_apikey_data():
    data = {
        "description": "userkey",
        "domains": ["example.org"],
        "role": "User"
    }
    return data


def admin_apikey_data():
    data = {"description": "masterkey", "domains": [], "role": "Administrator"}
    return data


@pytest.fixture(scope='module')
def user_apikey_integration(app):
    test_user_apikey = app.config.get('TEST_USER_APIKEY')
    headers = create_apikey_headers(test_user_apikey)
    return headers


@pytest.fixture(scope='module')
def admin_apikey_integration(app):
    test_user_apikey = app.config.get('TEST_ADMIN_APIKEY')
    headers = create_apikey_headers(test_user_apikey)
    return headers


@pytest.fixture(scope='module')
def user_apikey(app):
    with app.app_context():
        data = user_apikey_data()
        api_key = ApiKey(desc=data['description'],
                         role_name=data['role'],
                         domains=[])
        headers = create_apikey_headers(api_key.plain_key)
        return headers


@pytest.fixture(scope='module')
def admin_apikey(app):
    with app.app_context():
        data = admin_apikey_data()
        api_key = ApiKey(desc=data['description'],
                         role_name=data['role'],
                         domains=[])
        headers = create_apikey_headers(api_key.plain_key)
        return headers


def create_apikey_headers(passw):
    user_pass_base64 = b64encode(passw.encode('utf-8'))
    headers = {"X-API-KEY": "{0}".format(user_pass_base64.decode('utf-8'))}
    return headers


@pytest.fixture
def account_data():
    data = {
        "name": "test1",
        "description": "test1 account",
        "contact": "test1 contact",
        "mail": "test1@example.com",
    }
    return data


@pytest.fixture
def user1_data():
    data = {
        "username": "testuser1",
        "plain_text_password": "ChangeMePlease",
        "firstname": "firstname1",
        "lastname": "lastname1",
        "email": "testuser1@example.com",
        "otp_secret": "",
        "confirmed": False,
        "role_name": "User",
    }
    return data
