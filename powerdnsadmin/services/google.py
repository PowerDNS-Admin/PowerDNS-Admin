from flask import request, session, redirect, url_for, current_app

from .base import authlib_oauth_client
from ..models.setting import Setting


def google_oauth():
    if not Setting().get('google_oauth_enabled'):
        return None

    def fetch_google_token():
        return session.get('google_token')

    def update_token(token):
        session['google_token'] = token
        return token

    google = authlib_oauth_client.register(
        'google',
        client_id=Setting().get('google_oauth_client_id'),
        client_secret=Setting().get('google_oauth_client_secret'),
        api_base_url=Setting().get('google_base_url'),
        request_token_url=None,
        access_token_url=Setting().get('google_token_url'),
        authorize_url=Setting().get('google_authorize_url'),
        client_kwargs={'scope': Setting().get('google_oauth_scope')},
        fetch_token=fetch_google_token,
        update_token=update_token)

    @current_app.route('/google/authorized')
    def google_authorized():
        session['google_oauthredir'] = url_for(
            '.google_authorized', _external=True)
        token = google.authorize_access_token()
        if token is None:
            return 'Access denied: reason=%s error=%s' % (
                request.args['error_reason'],
                request.args['error_description']
            )
        session['google_token'] = (token)
        return redirect(url_for('index.login'))

    return google

