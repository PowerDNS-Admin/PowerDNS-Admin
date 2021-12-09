import os
import logging
from flask import Flask
from flask_seasurf import SeaSurf
from flask_mail import Mail
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_session import Session

from .lib import utils


def create_app(config=None, other=''):
    import urllib
    from . import models, routes, services
    from .assets import assets
    from .lib import config_util
    app = Flask(__name__)

    ########################################
    # LOGGING SETUP
    ########################################

    # Read log level from environment variable
    log_level_name = os.environ.get('PDNS_ADMIN_LOG_LEVEL', 'WARNING')
    log_level = logging.getLevelName(log_level_name.upper())
    # Setting logger
    logging.basicConfig(
       level=log_level,
        format=
        "[%(asctime)s] [%(filename)s:%(lineno)d] %(levelname)s - %(message)s")

    # Reconfigure the log handler if gunicorn is being ran in Docker
    if "PDA_GUNICORN_ENABLED" in os.environ and bool(os.environ['PDA_GUNICORN_ENABLED']):
        gunicorn_logger = logging.getLogger("gunicorn.error")
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

    # Proxy Support
    app.wsgi_app = ProxyFix(app.wsgi_app)

    ########################################
    # CSRF Protection Setup
    ########################################
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
    csrf.exempt(routes.api.api_create_account)
    csrf.exempt(routes.api.api_delete_account)
    csrf.exempt(routes.api.api_update_account)
    csrf.exempt(routes.api.api_create_user)
    csrf.exempt(routes.api.api_delete_user)
    csrf.exempt(routes.api.api_update_user)
    csrf.exempt(routes.api.api_list_account_users)
    csrf.exempt(routes.api.api_add_account_user)
    csrf.exempt(routes.api.api_remove_account_user)
    csrf.exempt(routes.api.api_zone_cryptokeys)
    csrf.exempt(routes.api.api_zone_cryptokey)

    ########################################
    # CONFIGURATION SETUP
    ########################################

    # Load default configuration
    app.config.from_object('configs.default')

    # Load config file from path given in FLASK_CONF env variable
    if 'FLASK_CONF' in os.environ:
        app.config.from_envvar('FLASK_CONF')

    # Load instance specific configuration
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif config.endswith('.py'):
            app.config.from_pyfile(config)

    # Load configuration from environment variables
    config_util.load_config_from_env(app)

    # If no SQLA DB URI is set but SQLA MySQL settings are present, then create DB URI setting
    if 'SQLALCHEMY_DATABASE_URI' not in app.config and 'SQLA_DB_USER' in app.config \
            and 'SQLA_DB_PASSWORD' in app.config and 'SQLA_DB_HOST' in app.config and 'SQLA_DB_PORT' in app.config \
            and 'SQLA_DB_NAME' in app.config:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{}:{}@{}:{}/{}'.format(
            urllib.parse.quote_plus(app.config.get('SQLA_DB_USER')),
            urllib.parse.quote_plus(app.config.get('SQLA_DB_PASSWORD')),
            app.config.get('SQLA_DB_HOST'),
            app.config.get('SQLA_DB_PORT'),
            app.config.get('SQLA_DB_NAME')
        )
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////srv/app/pdns.db'

    ########################################
    # SSL SETUP
    ########################################

    # HSTS
    if app.config.get('HSTS_ENABLED'):
        from flask_sslify import SSLify
        _sslify = SSLify(app)  # lgtm [py/unused-local-variable]

    ########################################
    # SESSION SETUP
    ########################################

    # Load Flask-Session
    if app.config.get('FILESYSTEM_SESSIONS_ENABLED'):
        app.config['SESSION_TYPE'] = 'filesystem'
        sess = Session()
        sess.init_app(app)

    ########################################
    # MAIL SETUP
    ########################################

    # SMTP
    app.mail = Mail(app)

    ########################################
    # FLASK APP SETUP
    ########################################

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
    app.jinja_env.filters['pretty_domain_name'] = utils.pretty_domain_name

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

    @app.context_processor
    def inject_mode():
        setting = app.config.get('OFFLINE_MODE', False)
        return dict(OFFLINE_MODE=setting)

    return app
