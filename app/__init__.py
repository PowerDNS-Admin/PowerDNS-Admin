from werkzeug.contrib.fixers import ProxyFix
from flask import Flask, request, session, redirect, url_for
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')
app.wsgi_app = ProxyFix(app.wsgi_app)

login_manager = LoginManager()
login_manager.init_app(app)
db = SQLAlchemy(app)

def enable_github_oauth(GITHUB_ENABLE):
    if not GITHUB_ENABLE:
        return None, None
    from flask_oauthlib.client import OAuth
    oauth = OAuth(app)
    github = oauth.remote_app(
        'github',
        consumer_key=app.config['GITHUB_OAUTH_KEY'],
        consumer_secret=app.config['GITHUB_OAUTH_SECRET'],
        request_token_params={'scope': app.config['GITHUB_OAUTH_SCOPE']},
        base_url=app.config['GITHUB_OAUTH_URL'],
        request_token_url=None,
        access_token_method='POST',
        access_token_url=app.config['GITHUB_OAUTH_TOKEN'],
        authorize_url=app.config['GITHUB_OAUTH_AUTHORIZE']
    )

    @app.route('/user/authorized')
    def authorized():
        session['github_oauthredir'] = url_for('.authorized', _external=True)
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

    return oauth, github

oauth, github = enable_github_oauth(app.config.get('GITHUB_OAUTH_ENABLE'))


from app import views, models
