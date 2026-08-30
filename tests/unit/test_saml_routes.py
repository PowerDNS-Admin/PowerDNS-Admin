import onelogin.saml2.utils as saml_utils
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
        events = History.query.filter_by(
            msg='Created user saml-history-user').all()
        assert len(events) == 1
        assert events[0].created_by == 'SAML Assertion'
