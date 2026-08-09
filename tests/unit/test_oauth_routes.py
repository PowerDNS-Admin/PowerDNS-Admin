from authlib.integrations.base_client.errors import MismatchingStateError

import powerdnsadmin.routes.index as index_routes
from powerdnsadmin.models.setting import Setting


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
