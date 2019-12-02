from flask import request, session, redirect, url_for, current_app

from .base import authlib_oauth_client
from ..models.setting import Setting


def github_oauth():
    if not Setting().get('github_oauth_enabled'):
        return None

    def fetch_github_token():
        return session.get('github_token')

    def update_token(token):
        session['google_token'] = token
        return token

    github = authlib_oauth_client.register(
        'github',
        client_id=Setting().get('github_oauth_key'),
        client_secret=Setting().get('github_oauth_secret'),
        request_token_params={'scope': Setting().get('github_oauth_scope')},
        api_base_url=Setting().get('github_oauth_api_url'),
        request_token_url=None,
        access_token_url=Setting().get('github_oauth_token_url'),
        authorize_url=Setting().get('github_oauth_authorize_url'),
        client_kwargs={'scope': Setting().get('github_oauth_scope')},
        fetch_token=fetch_github_token,
        update_token=update_token)

    @current_app.route('/github/authorized')
    def github_authorized():
        session['github_oauthredir'] = url_for('.github_authorized',
                                               _external=True)
        token = github.authorize_access_token()
        if token is None:
            return 'Access denied: reason=%s error=%s' % (
                request.args['error'], request.args['error_description'])
        session['github_token'] = (token)
        return redirect(url_for('index.login'))

    return github
