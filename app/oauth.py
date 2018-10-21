from ast import literal_eval
from flask import request, session, redirect, url_for

from app import app, oauth_client, authlib_oauth_client
from app.models import Setting

# TODO: 
#   - Replace Flask-OAuthlib by authlib
#   - Fix github/google enabling (Currently need to reload the flask app)

def github_oauth():
    if not Setting().get('github_oauth_enabled'):
        return None

    github = oauth_client.remote_app(
        'github',
        consumer_key = Setting().get('github_oauth_key'),
        consumer_secret = Setting().get('github_oauth_secret'),
        request_token_params = {'scope': Setting().get('github_oauth_scope')},
        base_url = Setting().get('github_oauth_api_url'),
        request_token_url = None,
        access_token_method = 'POST',
        access_token_url = Setting().get('github_oauth_token_url'),
        authorize_url = Setting().get('github_oauth_authorize_url')
    )

    @app.route('/github/authorized')
    def github_authorized():
        session['github_oauthredir'] = url_for('.github_authorized', _external=True)
        resp = github.authorized_response()
        if resp is None:
            return 'Access denied: reason=%s error=%s' % (
                request.args['error'],
                request.args['error_description']
            )
        session['github_token'] = (resp['access_token'], '')
        return redirect(url_for('.login'))

    @github.tokengetter
    def get_github_oauth_token():
        return session.get('github_token')

    return github


def google_oauth():
    if not Setting().get('google_oauth_enabled'):
        return None

    google = oauth_client.remote_app(
        'google',
        consumer_key=Setting().get('google_oauth_client_id'),
        consumer_secret=Setting().get('google_oauth_client_secret'),
        request_token_params=literal_eval(Setting().get('google_token_params')),
        base_url=Setting().get('google_base_url'),
        request_token_url=None,
        access_token_method='POST',
        access_token_url=Setting().get('google_token_url'),
        authorize_url=Setting().get('google_authorize_url'),
    )

    @app.route('/google/authorized')
    def google_authorized():
        resp = google.authorized_response()
        if resp is None:
            return 'Access denied: reason=%s error=%s' % (
                request.args['error_reason'],
                request.args['error_description']
            )
        session['google_token'] = (resp['access_token'], '')
        return redirect(url_for('.login'))

    @google.tokengetter
    def get_google_oauth_token():
        return session.get('google_token')

    return google

def oidc_oauth():
    if not Setting().get('oidc_oauth_enabled'):
        return None

    def fetch_oidc_token():
        return session.get('oidc_token')

    oidc = authlib_oauth_client.register(
        'oidc',
        client_id = Setting().get('oidc_oauth_key'),
        client_secret = Setting().get('oidc_oauth_secret'),
        api_base_url = Setting().get('oidc_oauth_api_url'),
        request_token_url = None,
        access_token_url = Setting().get('oidc_oauth_token_url'),
        authorize_url = Setting().get('oidc_oauth_authorize_url'),
        client_kwargs={'scope': Setting().get('oidc_oauth_scope')},
        fetch_token=fetch_oidc_token,
    )

    @app.route('/oidc/authorized')
    def oidc_authorized():
        session['oidc_oauthredir'] = url_for('.oidc_authorized', _external=True)
        token = oidc.authorize_access_token()
        if token is None:
            return 'Access denied: reason=%s error=%s' % (
                request.args['error'],
                request.args['error_description']
            )
        session['oidc_token'] = (token)
        return redirect(url_for('.login'))

    return oidc