import json

import onelogin.saml2.utils as saml_utils
from onelogin.saml2.auth import OneLogin_Saml2_Auth
import pytest
from flask import request

import powerdnsadmin.routes.saml as saml_routes
from powerdnsadmin.models.history import History
from powerdnsadmin.services.saml import SAML


class FakeSamlAuth:
    def process_response(self):
        pass

    def get_attributes(self):
        return {
            'username': ['saml-history-user'],
            'email': ['saml-history-user@example.test'],
            'givenname': ['SAML'],
            'surname': ['History'],
        }

    def get_errors(self):
        return []

    def get_nameid(self):
        return 'saml-history-user@example.test'

    def get_session_index(self):
        return 'saml-history-session'


class FakeSamlClient:
    def prepare_flask_request(self, request):
        return {'script_name': request.path}

    def init_saml_auth(self, request_data):
        return FakeSamlAuth()


def test_saml_redirect_signature_uses_exact_received_query_string(app):
    raw_query = (
        'SAMLResponse=response%2Bvalue%3D&RelayState=http%3A%2F%2Flocalhost'
        '%3A9191%2Flogout&SigAlg=rsa-sha256&Signature=signature%2Bvalue%3D')

    with app.test_request_context('/saml/sls?' + raw_query):
        request_data = SAML.__new__(SAML).prepare_flask_request(request)

    assert request_data['validate_signature_from_qs'] is True
    assert request_data['lowercase_urlencoding'] is False
    assert request_data['query_string'] == raw_query


def test_saml_lowercase_urlencoding_can_be_enabled_for_adfs(app):
    with app.test_request_context('/saml/login'):
        app.config['SAML_LOWERCASE_URLENCODING'] = True
        request_data = SAML.__new__(SAML).prepare_flask_request(request)

    assert request_data['validate_signature_from_qs'] is True
    assert request_data['lowercase_urlencoding'] is True


def test_saml_jit_user_creation_is_recorded_once_in_admin_history(
        app, client, initial_data, monkeypatch):
    monkeypatch.setitem(app.config, 'SAML_ENABLED', True)
    monkeypatch.setitem(app.config, 'SAML_ATTRIBUTE_USERNAME', 'username')
    monkeypatch.setitem(app.config, 'SAML_ATTRIBUTE_EMAIL', 'email')
    monkeypatch.setitem(app.config, 'SAML_ATTRIBUTE_GIVENNAME', 'givenname')
    monkeypatch.setitem(app.config, 'SAML_ATTRIBUTE_SURNAME', 'surname')
    monkeypatch.setattr(
        saml_utils.OneLogin_Saml2_Utils, 'get_self_url',
        staticmethod(lambda request_data: 'https://localhost'))
    with app.app_context():
        app.extensions[saml_routes._SAML_CLIENT_KEY] = FakeSamlClient()

    first_response = client.post('/saml/authorized')
    second_response = client.post('/saml/authorized')

    assert first_response.status_code == 302
    assert second_response.status_code == 302
    with app.app_context():
        events = History.query.filter(
            History.msg.startswith('Created user saml-history-user')).all()
        assert len(events) == 1
        assert events[0].created_by == 'SAML Assertion'
        assert events[0].msg == 'Created user saml-history-user'
        assert json.loads(events[0].detail)['ip_address'] == '127.0.0.1'


class RedirectSamlAuth(FakeSamlAuth):
    # Exercise the real library's redirect construction after simulating a
    # successfully validated SAML response, without requiring a live IdP.
    redirect_to = OneLogin_Saml2_Auth.redirect_to

    def __init__(self, request_data):
        self._request_data = request_data


class RedirectSamlClient:
    def prepare_flask_request(self, request):
        return SAML.__new__(SAML).prepare_flask_request(request)

    def init_saml_auth(self, request_data):
        return RedirectSamlAuth(request_data)


@pytest.fixture
def successful_saml(app, initial_data, monkeypatch):
    monkeypatch.setitem(app.config, 'SAML_ENABLED', True)
    monkeypatch.setitem(app.config, 'SAML_ATTRIBUTE_USERNAME', 'username')
    monkeypatch.setitem(app.config, 'SAML_ATTRIBUTE_EMAIL', 'email')
    monkeypatch.setitem(app.config, 'SAML_ATTRIBUTE_GIVENNAME', 'givenname')
    monkeypatch.setitem(app.config, 'SAML_ATTRIBUTE_SURNAME', 'surname')
    monkeypatch.setitem(app.extensions, saml_routes._SAML_CLIENT_KEY,
                        RedirectSamlClient())


@pytest.mark.parametrize('relay_state', [
    'https://attacker.example/harvest',
    'http://attacker.example/harvest',
    '//attacker.example/harvest',
    '///attacker.example/harvest',
    '/\\attacker.example/harvest',
    'https://localhost.attacker.example/harvest',
    'https://localhost@attacker.example/harvest',
    'https://attacker.example@localhost/harvest',
    'https://localhost:444/harvest',
    'http://localhost/harvest',
    'https:///attacker.example/harvest',
    'javascript:alert(1)',
    ' https://attacker.example/harvest',
    '/\t/attacker.example/harvest',
    '/\r\n/attacker.example/harvest',
    'https://localhost:invalid/harvest',
    'https://[invalid/harvest',
])
def test_saml_unsafe_relay_state_falls_back_to_normal_login(
        app, client, successful_saml, relay_state):
    response = client.post('/saml/authorized', base_url='https://localhost',
                           data={'RelayState': relay_state})

    assert response.status_code == 302
    assert response.headers['Location'] == '/login'
    with client.session_transaction() as session:
        assert session['authentication_type'] == 'SAML'
        assert session['_user_id']
        assert 'session_version' in session


@pytest.mark.parametrize(('base_url', 'relay_state', 'expected'), [
    ('http://localhost', '/dashboard/', 'http://localhost/dashboard/'),
    ('https://localhost', '/dashboard/?tab=zones#records',
     'https://localhost/dashboard/?tab=zones#records'),
    ('https://localhost', 'https://localhost/dashboard/',
     'https://localhost/dashboard/'),
    ('http://localhost', 'http://localhost:80/dashboard/',
     'http://localhost:80/dashboard/'),
    ('https://localhost', 'https://localhost:443/dashboard/',
     'https://localhost:443/dashboard/'),
    ('https://localhost:9191', 'https://localhost:9191/dashboard/',
     'https://localhost:9191/dashboard/'),
])
def test_saml_internal_relay_state_remains_supported(
        client, successful_saml, base_url, relay_state, expected):
    response = client.post('/saml/authorized', base_url=base_url,
                           data={'RelayState': relay_state})

    assert response.status_code == 302
    assert response.headers['Location'] == expected


@pytest.mark.parametrize('relay_state', ['', '/saml/authorized',
                                       'http://localhost/saml/authorized'])
def test_saml_empty_or_callback_relay_state_completes_login(
        client, successful_saml, relay_state):
    response = client.post('/saml/authorized', data={'RelayState': relay_state})

    assert response.status_code == 302
    assert response.headers['Location'] == '/login'
    with client.session_transaction() as session:
        assert session['_user_id']
