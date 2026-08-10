import json
from urllib.parse import parse_qs, urlsplit

import pytest
from authlib.integrations.base_client.errors import MismatchingStateError

import powerdnsadmin.routes.oauth as oauth_routes
from powerdnsadmin.models.history import History
from powerdnsadmin.models.setting import Setting


OAUTH_PROVIDERS = (
    ('google', 'google_oauth_enabled', 'google_token', 'error_reason'),
    ('github', 'github_oauth_enabled', 'github_token', 'error'),
    ('azure', 'azure_oauth_enabled', 'azure_token', 'error'),
    ('oidc', 'oidc_oauth_enabled', 'oidc_token', 'error'),
)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload)

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError('HTTP {}'.format(self.status_code))


def set_oauth_client(app, provider, fake_client):
    """Install a fake Authlib client on the app extensions cache."""
    with app.app_context():
        clients = app.extensions.get(oauth_routes._OAUTH_CLIENTS_KEY)
        if clients is None:
            clients = {
                'google': None,
                'github': None,
                'azure': None,
                'oidc': None,
            }
            app.extensions[oauth_routes._OAUTH_CLIENTS_KEY] = clients
        clients[provider] = fake_client


def completing_oauth_client(provider, token):
    """Fake client that exchanges a code and returns provider userinfo."""

    class FakeOAuthClient:
        def authorize_access_token(self):
            return token

        def authorize_redirect(self, redirect_uri):
            raise AssertionError('authorized callback should not redirect')

        def load_server_metadata(self):
            return {}

        def get(self, url, timeout=None):
            if provider == 'google':
                return FakeResponse({
                    'given_name': 'Ada',
                    'family_name': 'Lovelace',
                    'email': 'google-ada@example.com',
                })
            if provider == 'github':
                return FakeResponse({
                    'login': 'github-ada',
                    'name': 'Ada Lovelace',
                    'email': 'github-ada@example.com',
                })
            if provider == 'azure':
                return FakeResponse({
                    'displayName': 'Ada Lovelace',
                    'givenName': 'Ada',
                    'id': 'azure-id',
                    'mail': 'azure-ada@example.com',
                    'surname': 'Lovelace',
                    'userPrincipalName': 'azure-ada@example.com',
                })
            if provider == 'oidc':
                return FakeResponse({
                    'preferred_username': 'oidc-ada',
                    'given_name': 'Ada',
                    'family_name': 'Lovelace',
                    'email': 'oidc-ada@example.com',
                })
            raise AssertionError('unexpected get({})'.format(url))

        def post(self, url, json=None):
            if provider == 'azure' and 'getMemberGroups' in url:
                return FakeResponse({'value': []})
            raise AssertionError('unexpected post({})'.format(url))

    return FakeOAuthClient()


def test_oauth_callbacks_are_registered_during_application_setup(app):
    callback_endpoints = {
        rule.rule: rule.endpoint
        for rule in app.url_map.iter_rules()
        if rule.rule.endswith('/authorized')
    }

    assert callback_endpoints['/google/authorized'] == \
        'oauth.google_authorized'
    assert callback_endpoints['/github/authorized'] == \
        'oauth.github_authorized'
    assert callback_endpoints['/azure/authorized'] == \
        'oauth.azure_authorized'
    assert callback_endpoints['/oidc/authorized'] == \
        'oauth.oidc_authorized'


def test_saml_routes_are_registered_during_application_setup(app):
    saml_endpoints = {
        rule.rule: rule.endpoint
        for rule in app.url_map.iter_rules()
        if rule.rule.startswith('/saml/')
    }

    assert saml_endpoints['/saml/login'] == 'saml.saml_login'
    assert saml_endpoints['/saml/authorized'] == 'saml.saml_authorized'
    assert saml_endpoints['/saml/metadata'] == 'saml.saml_metadata'
    assert saml_endpoints['/saml/sls'] == 'saml.saml_logout'


@pytest.mark.parametrize(
    'provider,setting_key,token_session_key,reason_param', OAUTH_PROVIDERS)
@pytest.mark.parametrize('use_ssl,scheme', ((True, 'https'), (False, 'http')))
def test_oauth_login_uses_expected_external_callback_url(
        app, client, initial_data, monkeypatch, provider, setting_key,
        token_session_key, reason_param, use_ssl, scheme):
    class FakeOAuthClient:
        redirect_uri = None

        def authorize_redirect(self, redirect_uri):
            self.redirect_uri = redirect_uri
            return 'redirect started'

    fake_client = FakeOAuthClient()
    set_oauth_client(app, provider, fake_client)
    monkeypatch.setitem(app.config, 'SERVER_EXTERNAL_SSL', use_ssl)
    with app.app_context():
        assert Setting().set(setting_key, True)

    response = client.get(f'/{provider}/login')

    assert response.status_code == 200
    assert response.data == b'redirect started'
    assert fake_client.redirect_uri == \
        f'{scheme}://localhost/{provider}/authorized'


@pytest.mark.parametrize(
    'provider,setting_key,token_session_key,reason_param', OAUTH_PROVIDERS)
def test_oauth_callback_completes_login_after_token_exchange(
        app, client, initial_data, monkeypatch, provider, setting_key,
        token_session_key, reason_param):
    token = {'access_token': f'{provider}-access-token'}
    info_messages = []
    monkeypatch.setattr(
        app.logger, 'info',
        lambda message, *args: info_messages.append(message % args))
    set_oauth_client(app, provider, completing_oauth_client(provider, token))
    monkeypatch.setitem(app.config, 'SERVER_EXTERNAL_SSL', True)
    with app.app_context():
        assert Setting().set(setting_key, True)

    response = client.get(f'/{provider}/authorized')

    assert response.status_code == 302
    # authenticate_user() finishes with a relative redirect to /login
    assert response.headers['Location'].endswith('/login')
    with client.session_transaction() as oauth_session:
        assert oauth_session[token_session_key] == token
        assert oauth_session[f'{provider}_oauthredir'] == \
            f'https://localhost/{provider}/authorized'
        assert oauth_session.get('authentication_type') == 'OAuth'

    provider_labels = {
        'google': 'Google OAuth',
        'github': 'GitHub OAuth',
        'azure': 'Microsoft Entra ID OAuth',
        'oidc': 'OIDC',
    }
    assert any(
        '{} provisioning completed'.format(provider_labels[provider]) in
        message and 'local_user=created' in message
        for message in info_messages)

    second_response = client.get(f'/{provider}/authorized')
    assert second_response.status_code == 302

    provider_users = {
        'google': 'google-ada@example.com',
        'github': 'github-ada',
        'azure': 'azure-ada@example.com',
        'oidc': 'oidc-ada',
    }
    history_actors = {
        'google': 'Google OAuth',
        'github': 'GitHub OAuth',
        'azure': 'Microsoft Entra ID OAuth',
        'oidc': 'OIDC Assertion',
    }
    with app.app_context():
        events = History.query.filter_by(
            msg='Created user {}'.format(provider_users[provider])).all()
        assert len(events) == 1
        assert events[0].created_by == history_actors[provider]


@pytest.mark.parametrize(
    'provider,setting_key,token_session_key,reason_param', OAUTH_PROVIDERS)
def test_disabled_oauth_provider_rejects_login_and_callback(
        app, client, initial_data, monkeypatch, provider, setting_key,
        token_session_key, reason_param):
    class FakeOAuthClient:
        def authorize_redirect(self, redirect_uri):
            raise AssertionError(
                'disabled provider attempted an authorization redirect')

        def authorize_access_token(self):
            raise AssertionError('disabled provider attempted a token exchange')

    set_oauth_client(app, provider, FakeOAuthClient())
    with app.app_context():
        assert Setting().set(setting_key, False)

    assert client.get(f'/{provider}/login').status_code == 400
    assert client.get(f'/{provider}/authorized').status_code == 400


@pytest.mark.parametrize(
    'provider,setting_key,token_session_key,reason_param', OAUTH_PROVIDERS)
def test_oauth_access_denial_uses_provider_reason_parameter(
        app, client, initial_data, monkeypatch, provider, setting_key,
        token_session_key, reason_param):
    class FakeOAuthClient:
        def authorize_access_token(self):
            return None

    set_oauth_client(app, provider, FakeOAuthClient())
    with app.app_context():
        assert Setting().set(setting_key, True)

    response = client.get(
        f'/{provider}/authorized',
        query_string={
            reason_param: f'{provider}-denied',
            'error_description': f'{provider}-description',
        },
    )

    assert response.status_code == 400
    assert f'reason={provider}-denied'.encode() in response.data
    assert f'error={provider}-description'.encode() in response.data


def test_oidc_authorized_mismatching_state_clears_session_and_returns_login(
        app, client, initial_data, monkeypatch):
    class FakeOidcClient:
        def authorize_access_token(self):
            raise MismatchingStateError(
                'mismatching_state: CSRF Warning! State not equal in request and response.')

    with app.app_context():
        assert Setting().set('oidc_oauth_enabled', True)

    set_oauth_client(app, 'oidc', FakeOidcClient())

    with client.session_transaction() as session:
        session['oidc_token'] = {'access_token': 'stale'}
        session['next'] = '/dashboard'

    response = client.get(
        '/oidc/authorized',
        query_string={'code': 'unused', 'state': 'stale-state'},
    )

    assert response.status_code == 400
    assert b'Your sign-in session expired. Please try again.' in response.data
    assert b'login-card-body' in response.data

    with client.session_transaction() as session:
        assert 'oidc_token' not in session
        assert 'next' not in session
        assert '_user_id' not in session


def test_oidc_logout_uses_discovered_rp_initiated_logout_endpoint(
        app, client, initial_data, monkeypatch):
    class FakeOidcClient:
        def load_server_metadata(self):
            return {
                'end_session_endpoint':
                    'https://idp.example.test/oidc/logout?provider=value'
            }

    set_oauth_client(app, 'oidc', FakeOidcClient())
    monkeypatch.setitem(app.config, 'SERVER_EXTERNAL_SSL', True)
    with app.app_context():
        assert Setting().set('oidc_oauth_key', 'powerdns-admin')
        assert Setting().set('oidc_oauth_logout_url', '')

    with client.session_transaction() as oidc_session:
        oidc_session['oidc_token'] = {
            'access_token': 'access-token',
            'id_token': 'login-id-token',
        }

    response = client.get('/logout')

    assert response.status_code == 302
    location = urlsplit(response.headers['Location'])
    assert location.scheme == 'https'
    assert location.netloc == 'idp.example.test'
    assert location.path == '/oidc/logout'
    assert parse_qs(location.query) == {
        'provider': ['value'],
        'post_logout_redirect_uri': ['https://localhost/login'],
        'id_token_hint': ['login-id-token'],
        'client_id': ['powerdns-admin'],
    }
    with client.session_transaction() as oidc_session:
        assert 'oidc_token' not in oidc_session


def test_oidc_logout_uses_configured_endpoint_when_discovery_has_none(
        app, client, initial_data, monkeypatch):
    class FakeOidcClient:
        def load_server_metadata(self):
            return {}

    set_oauth_client(app, 'oidc', FakeOidcClient())
    monkeypatch.setitem(app.config, 'SERVER_EXTERNAL_SSL', False)
    with app.app_context():
        assert Setting().set('oidc_oauth_key', 'powerdns-admin')
        assert Setting().set(
            'oidc_oauth_logout_url',
            'https://fallback.example.test/session/end')

    with client.session_transaction() as oidc_session:
        oidc_session['oidc_token'] = {'access_token': 'access-token'}

    response = client.get('/logout')

    location = urlsplit(response.headers['Location'])
    assert location.netloc == 'fallback.example.test'
    assert parse_qs(location.query) == {
        'post_logout_redirect_uri': ['http://localhost/login'],
        'client_id': ['powerdns-admin'],
    }


def test_oidc_logout_without_provider_endpoint_still_clears_local_session(
        app, client, initial_data):
    class FakeOidcClient:
        def load_server_metadata(self):
            return {}

    set_oauth_client(app, 'oidc', FakeOidcClient())
    with app.app_context():
        assert Setting().set('oidc_oauth_logout_url', '')

    with client.session_transaction() as oidc_session:
        oidc_session['oidc_token'] = {'id_token': 'login-id-token'}

    response = client.get('/logout')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/login')
    with client.session_transaction() as oidc_session:
        assert 'oidc_token' not in oidc_session
