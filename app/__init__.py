from werkzeug.contrib.fixers import ProxyFix
from flask import Flask, request, session, redirect, url_for
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy as SA
from flask_migrate import Migrate


# subclass SQLAlchemy to enable pool_pre_ping
class SQLAlchemy(SA):
    def apply_pool_defaults(self, app, options):
        SA.apply_pool_defaults(self, app, options)
        options["pool_pre_ping"] = True


from app.assets import assets

app = Flask(__name__)
app.config.from_object('config')
app.wsgi_app = ProxyFix(app.wsgi_app)

assets.init_app(app)

#### CONFIGURE LOGGER ####
from app.lib.log import logger
logging = logger('powerdns-admin', app.config['LOG_LEVEL'], app.config['LOG_FILE']).config()

login_manager = LoginManager()
login_manager.init_app(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db) # used for flask-migrate

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


def enable_google_oauth(GOOGLE_ENABLE):
    if not GOOGLE_ENABLE:
        return None
    from flask_oauthlib.client import OAuth
    oauth = OAuth(app)

    google = oauth.remote_app(
        'google',
        consumer_key=app.config['GOOGLE_OAUTH_CLIENT_ID'],
        consumer_secret=app.config['GOOGLE_OAUTH_CLIENT_SECRET'],
        request_token_params=app.config['GOOGLE_TOKEN_PARAMS'],
        base_url=app.config['GOOGLE_BASE_URL'],
        request_token_url=None,
        access_token_method='POST',
        access_token_url=app.config['GOOGLE_TOKEN_URL'],
        authorize_url=app.config['GOOGLE_AUTHORIZE_URL'],
    )

    @app.route('/user/authorized')
    def authorized():
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


google = enable_google_oauth(app.config.get('GOOGLE_OAUTH_ENABLE'))

from app import views, models

if app.config.get('SAML_ENABLED') and app.config.get('SAML_ENCRYPT'):
    from app.lib import certutil
    if not certutil.check_certificate():
        certutil.create_self_signed_cert()
