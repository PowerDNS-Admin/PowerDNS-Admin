from collections.abc import Mapping

from flask import session

from .base import authlib_oauth_client
from ..models.setting import Setting


def _ensure_openid_scope(configured_scope):
    """Return an OIDC scope string containing the required openid scope."""
    scopes = configured_scope.split() if configured_scope else []
    if 'openid' not in scopes:
        scopes.insert(0, 'openid')
    return ' '.join(scopes)


def merge_oidc_claims(token, userinfo):
    """Combine validated ID-token claims with UserInfo endpoint claims."""
    claims = {}
    if isinstance(token, Mapping):
        token_userinfo = token.get('userinfo')
        if isinstance(token_userinfo, Mapping):
            claims.update(token_userinfo)
    if isinstance(userinfo, Mapping):
        claims.update(userinfo)
    return claims


def oidc_oauth():
    if not Setting().get('oidc_oauth_enabled'):
        return None

    def fetch_oidc_token():
        return session.get('oidc_token')

    def update_token(token):
        session['oidc_token'] = token
        return token

    authlib_params = {
        'client_id': Setting().get('oidc_oauth_key'),
        'client_secret': Setting().get('oidc_oauth_secret'),
        'api_base_url': Setting().get('oidc_oauth_api_url'),
        'request_token_url': None,
        'client_kwargs': {
            'scope': _ensure_openid_scope(
                Setting().get('oidc_oauth_scope'))
        },
        'fetch_token': fetch_oidc_token,
        'update_token': update_token
    }

    auto_configure = Setting().get('oidc_oauth_auto_configure')
    server_metadata_url = Setting().get('oidc_oauth_metadata_url')

    if auto_configure and isinstance(server_metadata_url, str) and len(server_metadata_url.strip()) > 0:
        authlib_params['server_metadata_url'] = server_metadata_url
    else:
        authlib_params['access_token_url'] = Setting().get('oidc_oauth_token_url')
        authlib_params['authorize_url'] = Setting().get('oidc_oauth_authorize_url')

    oidc = authlib_oauth_client.register(
        'oidc',
        **authlib_params
    )

    return oidc
