from flask import session
from flask_session.sqlalchemy import SqlAlchemySessionInterface

from powerdnsadmin.routes.auth_session import clear_session


def test_app_uses_sqlalchemy_session_backend_from_test_config(app):
    assert app.config['SESSION_TYPE'] == 'sqlalchemy'
    assert isinstance(app.session_interface, SqlAlchemySessionInterface)


def test_login_page_persists_csrf_token_in_configured_session(
        initial_data, client):
    login_response = client.get('/login')

    assert login_response.status_code == 200
    assert client.get_cookie('session') is not None

    with client.session_transaction() as session:
        assert session.get('_csrf_token')


def test_clear_session_removes_all_authentication_state(app):
    authentication_state = {
        'user_id': 1,
        'github_token': {'access_token': 'github'},
        'google_token': {'access_token': 'google'},
        'azure_token': {'access_token': 'azure'},
        'oidc_token': {'access_token': 'oidc'},
        'authentication_type': 'SAML',
        'remote_user': 'remote-user',
        'github_oauthredir': 'https://example.test/github/authorized',
        'google_oauthredir': 'https://example.test/google/authorized',
        'azure_oauthredir': 'https://example.test/azure/authorized',
        'oidc_oauthredir': 'https://example.test/oidc/authorized',
        'samlUserdata': {'groups': ['example']},
        'samlNameId': 'user@example.test',
        'samlSessionIndex': 'saml-session',
        'pending_totp_user_id': 1,
        'pending_totp_auth_method': 'LOCAL',
        'pending_totp_remember': True,
        'welcome_user_id': 1,
        'next': '/dashboard',
        '_state_oidc_random': {'data': {'state': 'random'}},
    }

    with app.test_request_context():
        session.update(authentication_state)
        session['_csrf_token'] = 'keep-csrf-token'

        clear_session()

        for key in authentication_state:
            assert key not in session
        assert session['_csrf_token'] == 'keep-csrf-token'
