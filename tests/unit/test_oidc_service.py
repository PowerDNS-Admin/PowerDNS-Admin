from powerdnsadmin.services.oidc import _ensure_openid_scope, merge_oidc_claims


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
