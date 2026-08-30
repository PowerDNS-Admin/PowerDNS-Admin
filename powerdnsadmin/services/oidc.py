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

    def update_token(token, **kwargs):
        # Authlib may call update_token with extra keyword arguments such as
        # `refresh_token` or `access_token` that were used to obtain the new
        # token.  Accept them gracefully so the callback never raises
        # "unexpected keyword argument".
        #
        # Merge semantics:
        #  1. Start from the existing session token when it is a mapping so
        #     that stable fields (e.g. refresh_token) already stored are not
        #     silently dropped when the IdP returns a partial token response.
        #  2. Overlay the incoming `token` mapping on top (new access_token /
        #     expires_at always win).
        #  3. If Authlib passed a `refresh_token` kwarg and the merged result
        #     still has no refresh_token entry, store it explicitly so the
        #     next refresh attempt has a valid grant.
        #  4. Ignore non-mapping `token` values to stay defensive.
        merged = {}
        existing = session.get('oidc_token')
        if isinstance(existing, Mapping):
            merged.update(existing)
        if isinstance(token, Mapping):
            merged.update(token)
        # Preserve kwargs-supplied token fields that are absent from the merged
        # result.  Semantics per-field:
        #  - refresh_token: Authlib passes the old refresh_token that was
        #    consumed to obtain this new token.  Preserve it only when the
        #    IdP's response omits a new one (RFC 6749 §6 allows reuse).
        #  - access_token: Authlib may pass the old access_token as context.
        #    It is a *fallback* only – the new token mapping always takes
        #    precedence, so it is stored only when completely absent.
        for field in ('refresh_token', 'access_token'):
            if field in kwargs and field not in merged:
                merged[field] = kwargs[field]
        session['oidc_token'] = merged
        return merged

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
