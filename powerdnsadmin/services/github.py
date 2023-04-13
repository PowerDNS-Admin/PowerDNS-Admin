from flask import request, session, redirect, url_for, current_app

from .base import authlib_oauth_client
from ..models.setting import Setting


def github_oauth():
    if not Setting().get('github_oauth_enabled'):
        return None

    def fetch_github_token():
        return session.get('github_token')

    def update_token(token):
        session['github_token'] = token
        return token

    authlib_params = {
        'client_id': Setting().get('github_oauth_key'),
        'client_secret': Setting().get('github_oauth_secret'),
        'request_token_params': {'scope': Setting().get('github_oauth_scope')},
        'api_base_url': Setting().get('github_oauth_api_url'),
        'request_token_url': None,
        'client_kwargs': {'scope': Setting().get('github_oauth_scope')},
        'fetch_token': fetch_github_token,
        'update_token': update_token
    }

    auto_configure = Setting().get('github_oauth_auto_configure')
    server_metadata_url = Setting().get('github_oauth_metadata_url')

    if auto_configure and isinstance(server_metadata_url, str) and len(server_metadata_url.strip()) > 0:
        authlib_params['server_metadata_url'] = server_metadata_url
    else:
        authlib_params['access_token_url'] = Setting().get('github_oauth_token_url')
        authlib_params['authorize_url'] = Setting().get('github_oauth_authorize_url')

    github = authlib_oauth_client.register(
        'github',
        **authlib_params
    )

    @current_app.route('/github/authorized')
    def github_authorized():
        use_ssl = current_app.config.get('SERVER_EXTERNAL_SSL')
        params = {'_external': True}
        if isinstance(use_ssl, bool):
            params['_scheme'] = 'https' if use_ssl else 'http'
        session['github_oauthredir'] = url_for('.github_authorized', **params)
        token = github.authorize_access_token()
        if token is None:
            return 'Access denied: reason=%s error=%s' % (
                request.args['error'], request.args['error_description'])
        session['github_token'] = token
        return redirect(url_for('index.login', **params))

    return github
