from flask import request, session, redirect, url_for, current_app

from .base import authlib_oauth_client
from ..models.setting import Setting


def azure_oauth():
    if not Setting().get('azure_oauth_enabled'):
        return None

    def fetch_azure_token():
        return session.get('azure_token')

    azure = authlib_oauth_client.register(
        'azure',
        client_id=Setting().get('azure_oauth_key'),
        client_secret=Setting().get('azure_oauth_secret'),
        api_base_url=Setting().get('azure_oauth_api_url'),
        request_token_url=None,
        access_token_url=Setting().get('azure_oauth_token_url'),
        authorize_url=Setting().get('azure_oauth_authorize_url'),
        client_kwargs={'scope': Setting().get('azure_oauth_scope')},
        fetch_token=fetch_azure_token,
    )

    @current_app.route('/azure/authorized')
    def azure_authorized():
        session['azure_oauthredir'] = url_for('.azure_authorized',
                                              _external=True,
                                              _scheme='https')
        token = azure.authorize_access_token()
        if token is None:
            return 'Access denied: reason=%s error=%s' % (
                request.args['error'], request.args['error_description'])
        session['azure_token'] = (token)
        return redirect(url_for('.login', _external=True, _scheme='https'))

    return azure
