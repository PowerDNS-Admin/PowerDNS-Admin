from powerdnsadmin.services.oidc import _ensure_openid_scope, merge_oidc_claims


# ---------------------------------------------------------------------------
# Helpers for update_token tests
# ---------------------------------------------------------------------------

def _make_update_token(session_store):
    """Return an update_token closure that uses *session_store* as the session."""
    from collections.abc import Mapping

    def update_token(token, **kwargs):
        merged = {}
        existing = session_store.get('oidc_token')
        if isinstance(existing, Mapping):
            merged.update(existing)
        if isinstance(token, Mapping):
            merged.update(token)
        for field in ('refresh_token', 'access_token'):
            if field in kwargs and field not in merged:
                merged[field] = kwargs[field]
        session_store['oidc_token'] = merged
        return merged

    return update_token


def test_ensure_openid_scope_adds_required_scope():
    assert _ensure_openid_scope('email profile') == 'openid email profile'


def test_ensure_openid_scope_preserves_configured_scope():
    assert _ensure_openid_scope('profile openid email') == 'profile openid email'


def test_ensure_openid_scope_handles_empty_scope():
    assert _ensure_openid_scope('') == 'openid'


def test_merge_oidc_claims_preserves_id_token_claims_missing_from_userinfo():
    token = {
        'userinfo': {
            'preferred_username': 'user@example.com',
            'name': 'ID token name',
        }
    }

    claims = merge_oidc_claims(token, {'name': 'Current name'})

    assert claims == {
        'preferred_username': 'user@example.com',
        'name': 'Current name',
    }


def test_merge_oidc_claims_handles_token_without_userinfo():
    assert merge_oidc_claims({'access_token': 'token'}, {'sub': '123'}) == {
        'sub': '123'
    }


# ---------------------------------------------------------------------------
# update_token tests
# ---------------------------------------------------------------------------

def test_update_token_accepts_refresh_token_kwarg():
    """Authlib may call update_token(token, refresh_token=...) – must not raise."""
    session = {}
    update_token = _make_update_token(session)
    result = update_token({'access_token': 'new_access'}, refresh_token='rt123')
    assert result['access_token'] == 'new_access'
    assert session['oidc_token']['access_token'] == 'new_access'


def test_update_token_preserves_refresh_token_from_kwargs_when_absent_in_new_token():
    """When new token omits refresh_token but kwarg provides it, it must be stored."""
    session = {}
    update_token = _make_update_token(session)
    result = update_token({'access_token': 'new_access'}, refresh_token='kwarg_rt')
    assert result['refresh_token'] == 'kwarg_rt'
    assert session['oidc_token']['refresh_token'] == 'kwarg_rt'


def test_update_token_new_token_refresh_token_takes_precedence_over_kwarg():
    """When new token already has refresh_token, it wins over kwarg."""
    session = {}
    update_token = _make_update_token(session)
    result = update_token(
        {'access_token': 'new_access', 'refresh_token': 'token_rt'},
        refresh_token='kwarg_rt',
    )
    assert result['refresh_token'] == 'token_rt'


def test_update_token_preserves_refresh_token_from_existing_session():
    """Existing session refresh_token is preserved when new token omits it."""
    session = {'oidc_token': {'access_token': 'old', 'refresh_token': 'session_rt'}}
    update_token = _make_update_token(session)
    result = update_token({'access_token': 'new_access'})
    assert result['refresh_token'] == 'session_rt'
    assert result['access_token'] == 'new_access'


def test_update_token_new_token_overwrites_stale_access_token():
    """New token access_token overwrites stale one from session."""
    session = {'oidc_token': {'access_token': 'old', 'refresh_token': 'rt'}}
    update_token = _make_update_token(session)
    result = update_token({'access_token': 'fresh'})
    assert result['access_token'] == 'fresh'
    assert result['refresh_token'] == 'rt'


def test_update_token_handles_non_mapping_existing_session():
    """Non-mapping garbage in session is silently ignored."""
    session = {'oidc_token': 'not-a-dict'}
    update_token = _make_update_token(session)
    result = update_token({'access_token': 'new'})
    assert result == {'access_token': 'new'}


def test_update_token_handles_non_mapping_token():
    """Non-mapping incoming token does not crash and produces empty merged dict."""
    session = {}
    update_token = _make_update_token(session)
    result = update_token(None)
    assert result == {}
    assert session['oidc_token'] == {}
