from flask import request, session, redirect, url_for, current_app

from .base import authlib_oauth_client
from ..models.setting import Setting


def oidc_oauth():
    if not Setting().get('oidc_oauth_enabled'):
        return None

    def fetch_oidc_token():
        return session.get('oidc_token')

    def update_token(token):
        session['google_token'] = token
        return token

    oidc = authlib_oauth_client.register(
        'oidc',
        client_id=Setting().get('oidc_oauth_key'),
        client_secret=Setting().get('oidc_oauth_secret'),
        api_base_url=Setting().get('oidc_oauth_api_url'),
        request_token_url=None,
        access_token_url=Setting().get('oidc_oauth_token_url'),
        authorize_url=Setting().get('oidc_oauth_authorize_url'),
        client_kwargs={'scope': Setting().get('oidc_oauth_scope')},
        fetch_token=fetch_oidc_token,
        update_token=update_token)

    @current_app.route('/oidc/authorized')
    def oidc_authorized():
        session['oidc_oauthredir'] = url_for('.oidc_authorized',
                                             _external=True)
        token = oidc.authorize_access_token()
        if token is None:
            return 'Access denied: reason=%s error=%s' % (
                request.args['error'], request.args['error_description'])
        session['oidc_token'] = (token)
        return redirect(url_for('index.login'))

    return oidc