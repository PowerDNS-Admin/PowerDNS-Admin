import os
import logging
from flask import Flask
from flask_seasurf import SeaSurf
from flask_mail import Mail
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_session import Session

from .lib import utils


def create_app(config=None):
    from . import models, routes, services
    from .assets import assets
    app = Flask(__name__)

    # Read log level from environment variable
    log_level_name = os.environ.get('PDNS_ADMIN_LOG_LEVEL', 'WARNING')
    log_level = logging.getLevelName(log_level_name.upper())
    # Setting logger
    logging.basicConfig(
       level=log_level,
        format=
        "[%(asctime)s] [%(filename)s:%(lineno)d] %(levelname)s - %(message)s")

    # If we use Docker + Gunicorn, adjust the
    # log handler
    if "GUNICORN_LOGLEVEL" in os.environ:
        gunicorn_logger = logging.getLogger("gunicorn.error")
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

    # Proxy
    app.wsgi_app = ProxyFix(app.wsgi_app)

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
    csrf.exempt(routes.api.api_create_account)
    csrf.exempt(routes.api.api_delete_account)
    csrf.exempt(routes.api.api_update_account)
    csrf.exempt(routes.api.api_create_user)
    csrf.exempt(routes.api.api_delete_user)
    csrf.exempt(routes.api.api_update_user)
    csrf.exempt(routes.api.api_list_account_users)
    csrf.exempt(routes.api.api_add_account_user)
    csrf.exempt(routes.api.api_remove_account_user)

    # Load config from env variables if using docker
    if os.path.exists(os.path.join(app.root_path, 'docker_config.py')):
        app.config.from_object('powerdnsadmin.docker_config')
    else:
        # Load default configuration
        app.config.from_object('powerdnsadmin.default_config')

    # Load config file from FLASK_CONF env variable
    if 'FLASK_CONF' in os.environ:
        app.config.from_envvar('FLASK_CONF')

    # Load app sepecified configuration
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif config.endswith('.py'):
            app.config.from_pyfile(config)

    # HSTS
    if app.config.get('HSTS_ENABLED'):
        from flask_sslify import SSLify
        _sslify = SSLify(app)  # lgtm [py/unused-local-variable]

    # Load Flask-Session
    if app.config.get('FILESYSTEM_SESSIONS_ENABLED'):
        app.config['SESSION_TYPE'] = 'filesystem'
        sess = Session()
        sess.init_app(app)

    # SMTP
    app.mail = Mail(app)

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
