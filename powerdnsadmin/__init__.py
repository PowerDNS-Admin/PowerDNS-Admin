import os
from werkzeug.contrib.fixers import ProxyFix
from flask import Flask
from flask_seasurf import SeaSurf
from flask_sslify import SSLify

from .lib import utils

# from flask_login import LoginManager
# from flask_sqlalchemy import SQLAlchemy as SA
# from flask_migrate import Migrate
# from authlib.flask.client import OAuth as AuthlibOAuth
# from sqlalchemy.exc import OperationalError

# from app.assets import assets

# ### SYBPATCH ###
# from app.customboxes import customBoxes
### SYBPATCH ###

# subclass SQLAlchemy to enable pool_pre_ping
# class SQLAlchemy(SA):
#     def apply_pool_defaults(self, app, options):
#         SA.apply_pool_defaults(self, app, options)
#         options["pool_pre_ping"] = True

# app = Flask(__name__)
# app.config.from_object('config')
# app.wsgi_app = ProxyFix(app.wsgi_app)
# csrf = SeaSurf(app)

# assets.init_app(app)

# #### CONFIGURE LOGGER ####
# from app.lib.log import logger
# logging = logger('powerdns-admin', app.config['LOG_LEVEL'], app.config['LOG_FILE']).config()

# login_manager = LoginManager()
# login_manager.init_app(app)
# db = SQLAlchemy(app)            # database
# migrate = Migrate(app, db)      # flask-migrate
# authlib_oauth_client = AuthlibOAuth(app) # authlib oauth

# if app.config.get('SAML_ENABLED') and app.config.get('SAML_ENCRYPT'):
#     from app.lib import certutil
#     if not certutil.check_certificate():
#         certutil.create_self_signed_cert()

# from app import models

# from app.blueprints.api import api_blueprint

# app.register_blueprint(api_blueprint, url_prefix='/api/v1')

# from app import views


def create_app(config=None):
    from . import models, routes, services
    from .assets import assets
    app = Flask(__name__)

    # Proxy
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # HSTS enabled
    _sslify = SSLify(app)

    # CSRF protection
    csrf = SeaSurf(app)
    csrf.exempt(routes.index.dyndns_checkip)
    csrf.exempt(routes.index.dyndns_update)
    csrf.exempt(routes.index.saml_authorized)
    csrf.exempt(routes.api.api_login_create_zone)
    csrf.exempt(routes.api.api_login_delete_zone)
    csrf.exempt(routes.api.api_generate_apikey)
    csrf.exempt(routes.api.api_delete_apikey)
    csrf.exempt(routes.api.api_update_apikey)
    csrf.exempt(routes.api.api_zone_subpath_forward)
    csrf.exempt(routes.api.api_zone_forward)
    csrf.exempt(routes.api.api_create_zone)

    # Load default configuration
    app.config.from_object('powerdnsadmin.default_config')

    # Load environment configuration
    if 'FLASK_CONF' in os.environ:
        app.config.from_envvar('FLASK_CONF')

    # Load app sepecified configuration
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif config.endswith('.py'):
            app.config.from_pyfile(config)

    # Load app's components
    assets.init_app(app)
    models.init_app(app)
    routes.init_app(app)
    services.init_app(app)

    # Register filters
    app.jinja_env.filters['display_record_name'] = utils.display_record_name
    app.jinja_env.filters['display_master_name'] = utils.display_master_name
    app.jinja_env.filters['display_second_to_time'] = utils.display_time
    app.jinja_env.filters[
        'email_to_gravatar_url'] = utils.email_to_gravatar_url
    app.jinja_env.filters[
        'display_setting_state'] = utils.display_setting_state

    # Register context proccessors
    from .models.setting import Setting

    @app.context_processor
    def inject_sitename():
        setting = Setting().get('site_name')
        return dict(SITE_NAME=setting)

    @app.context_processor
    def inject_setting():
        setting = Setting()
        return dict(SETTING=setting)

    return app