import os
import logging
from flask import Flask
from flask_mail import Mail
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_session import Session
from .lib import utils


def create_app(config=None):
    from powerdnsadmin.lib.settings import AppSettings
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

    # Verbose SQLAlchemy pool logging only in debug mode. The development
    # Compose scenario runs `flask run --debug` (sets FLASK_DEBUG); operators
    # can also raise PDNS_ADMIN_LOG_LEVEL=DEBUG without Flask debug.
    flask_debug = os.environ.get('FLASK_DEBUG', '').lower() in (
        '1', 'true', 'yes', 'on')
    if log_level == logging.DEBUG or flask_debug:
        logging.getLogger('sqlalchemy.pool').setLevel(logging.DEBUG)

    # If we use Docker + Gunicorn, adjust the
    # log handler
    if "GUNICORN_LOGLEVEL" in os.environ:
        gunicorn_logger = logging.getLogger("gunicorn.error")
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

    # Proxy
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # Load config from env variables if using docker
    if os.path.exists(os.path.join(app.root_path, 'docker_config.py')):
        app.config.from_object('powerdnsadmin.docker_config')
    else:
        # Load default configuration
        app.config.from_object('powerdnsadmin.default_config')

    # Load config file from FLASK_CONF env variable
    if 'FLASK_CONF' in os.environ:
        app.config.from_envvar('FLASK_CONF')

    # Load app specified configuration
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif config.endswith('.py'):
            app.config.from_pyfile(config)

    # Load any settings defined with environment variables
    AppSettings.load_environment(app)

    # Single source of truth for Docker and bare-metal deployments.
    app.config['APP_VERSION'] = utils.read_app_version(app.root_path)

    # HSTS
    if app.config.get('HSTS_ENABLED'):
        from flask_sslify import SSLify
        _sslify = SSLify(app)  # lgtm [py/unused-local-variable]

    # Flask-SQLAlchemy 3 requires the application database to be initialized
    # before extensions such as Flask-Session access it.
    models.init_app(app)

    # Load Flask-Session
    app.config['SESSION_TYPE'] = app.config.get('SESSION_TYPE')
    if 'SESSION_TYPE' in os.environ:
        app.config['SESSION_TYPE'] = os.environ.get('SESSION_TYPE')

    if app.config.get('SESSION_TYPE') == 'sqlalchemy':
        app.config['SESSION_SQLALCHEMY'] = models.db

    Session(app)

    # SMTP
    app.mail = Mail(app)

    # Load app's components
    if os.environ.get('POWERDNSADMIN_ASSETS_PREBUILT') == '1':
        # Docker images contain generated bundles but intentionally omit the
        # Node/Yarn toolchain and source dependency tree.
        app.config['ASSETS_AUTO_BUILD'] = False
    assets.init_app(app)
    routes.init_app(app)
    services.init_app(app)

    # Register filters
    app.jinja_env.filters['display_record_name'] = utils.display_record_name
    app.jinja_env.filters['display_master_name'] = utils.display_master_name
    app.jinja_env.filters['display_second_to_time'] = utils.display_time
    app.jinja_env.filters['display_setting_state'] = utils.display_setting_state
    app.jinja_env.filters['pretty_domain_name'] = utils.pretty_domain_name
    app.jinja_env.filters['format_datetime_local'] = utils.format_datetime
    app.jinja_env.filters['format_zone_type'] = utils.format_zone_type

    # Register context processors
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
    def inject_app_version():
        return dict(APP_VERSION=app.config['APP_VERSION'])

    return app