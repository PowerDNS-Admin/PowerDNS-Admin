import onelogin.saml2.utils as saml_utils
import pytest
from flask import request
from onelogin.saml2.auth import OneLogin_Saml2_Auth

import powerdnsadmin.routes.saml as saml_routes
from powerdnsadmin.models.history import History
from powerdnsadmin.services.saml import SAML


class FakeSamlAuth(OneLogin_Saml2_Auth):
    def __init__(self, request_data):
        self._request_data = request_data

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
        return SAML.__new__(SAML).prepare_flask_request(request)

    def init_saml_auth(self, request_data):
        return FakeSamlAuth(request_data)


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


@pytest.mark.parametrize('relay_state', [
    None,
    '',
    'https://localhost/saml/authorized',
    'https://attacker.example/phishing',
    'http://attacker.example/phishing',
    '//attacker.example/phishing',
    '/dashboard',
    r'/\attacker.example/phishing',
    'https://localhost@attacker.example/phishing',
])
def test_saml_login_ignores_relay_state_and_records_user_creation_once(
        app, client, initial_data, monkeypatch, relay_state):
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

    data = {} if relay_state is None else {'RelayState': relay_state}
    first_response = client.post('/saml/authorized', data=data)
    second_response = client.post('/saml/authorized', data=data)

    assert first_response.status_code == 302
    assert second_response.status_code == 302
    assert first_response.location == '/login'
    assert second_response.location == '/login'
    with client.session_transaction() as session:
        assert session['authentication_type'] == 'SAML'
        assert session['_user_id'] == str(session['user_id'])
    with app.app_context():
        events = History.query.filter_by(
            msg='Created user saml-history-user').all()
        assert len(events) == 1
        assert events[0].created_by == 'SAML Assertion'
