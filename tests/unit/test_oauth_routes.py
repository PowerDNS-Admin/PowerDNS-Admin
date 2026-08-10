import pytest
from authlib.integrations.base_client.errors import MismatchingStateError

import powerdnsadmin.routes.index as index_routes
from powerdnsadmin.models.setting import Setting


OAUTH_PROVIDERS = (
    ('google', 'google_oauth_enabled', 'google_token', 'error_reason'),
    ('github', 'github_oauth_enabled', 'github_token', 'error'),
    ('azure', 'azure_oauth_enabled', 'azure_token', 'error'),
    ('oidc', 'oidc_oauth_enabled', 'oidc_token', 'error'),
)


def prepare_oauth_client(client, monkeypatch, provider, fake_client):
    """Let the app register its auth modules before replacing one client."""
    assert client.get('/ping').status_code == 200
    monkeypatch.setattr(index_routes, provider, fake_client)


def test_oauth_callbacks_are_registered_during_application_setup(app):
    callback_endpoints = {
        rule.rule: rule.endpoint
        for rule in app.url_map.iter_rules()
        if rule.rule.endswith('/authorized')
    }

    assert callback_endpoints['/google/authorized'] == \
        'index.google_authorized'
    assert callback_endpoints['/github/authorized'] == \
        'index.github_authorized'
    assert callback_endpoints['/azure/authorized'] == \
        'index.azure_authorized'
    assert callback_endpoints['/oidc/authorized'] == \
        'index.oidc_authorized'


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
    prepare_oauth_client(client, monkeypatch, provider, fake_client)
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
def test_oauth_callback_stores_provider_session_values(
        app, client, initial_data, monkeypatch, provider, setting_key,
        token_session_key, reason_param):
    token = {'access_token': f'{provider}-access-token'}

    class FakeOAuthClient:
        def authorize_access_token(self):
            return token

    prepare_oauth_client(client, monkeypatch, provider, FakeOAuthClient())
    monkeypatch.setitem(app.config, 'SERVER_EXTERNAL_SSL', True)
    with app.app_context():
        assert Setting().set(setting_key, True)

    response = client.get(f'/{provider}/authorized')

    assert response.status_code == 302
    assert response.headers['Location'] == 'https://localhost/login'
    with client.session_transaction() as oauth_session:
        assert oauth_session[token_session_key] == token
        assert oauth_session[f'{provider}_oauthredir'] == \
            f'https://localhost/{provider}/authorized'


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

    prepare_oauth_client(client, monkeypatch, provider, FakeOAuthClient())
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

    prepare_oauth_client(client, monkeypatch, provider, FakeOAuthClient())
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

    # register_modules caches the OAuth clients on first request. Patch the
    # module-level client the route actually uses, not oidc_oauth().
    monkeypatch.setattr(index_routes, 'oidc', FakeOidcClient())

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
