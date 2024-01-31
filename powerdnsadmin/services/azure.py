from flask import request, session, redirect, url_for, current_app

from .base import authlib_oauth_client
from ..models.setting import Setting


def azure_oauth():
    if not Setting().get('azure_oauth_enabled'):
        return None

    def fetch_azure_token():
        return session.get('azure_token')

    def update_token(token):
        session['azure_token'] = token
        return token

    authlib_params = {
        'client_id': Setting().get('azure_oauth_key'),
        'client_secret': Setting().get('azure_oauth_secret'),
        'api_base_url': Setting().get('azure_oauth_api_url'),
        'request_token_url': None,
        'client_kwargs': {'scope': Setting().get('azure_oauth_scope')},
        'fetch_token': fetch_azure_token,
    }

    auto_configure = Setting().get('azure_oauth_auto_configure')
    server_metadata_url = Setting().get('azure_oauth_metadata_url')

    if auto_configure and isinstance(server_metadata_url, str) and len(server_metadata_url.strip()) > 0:
        authlib_params['server_metadata_url'] = server_metadata_url
    else:
        authlib_params['access_token_url'] = Setting().get('azure_oauth_token_url')
        authlib_params['authorize_url'] = Setting().get('azure_oauth_authorize_url')

    azure = authlib_oauth_client.register(
        'azure',
        **authlib_params
    )

    @current_app.route('/azure/authorized')
    def azure_authorized():
        use_ssl = current_app.config.get('SERVER_EXTERNAL_SSL')
        params = {'_external': True}
        if isinstance(use_ssl, bool):
            params['_scheme'] = 'https' if use_ssl else 'http'
        session['azure_oauthredir'] = url_for('.azure_authorized', **params)
        token = azure.authorize_access_token()
        if token is None:
            return 'Access denied: reason=%s error=%s' % (
                request.args['error'], request.args['error_description'])
        session['azure_token'] = (token)
        return redirect(url_for('index.login', **params))

    return azure
