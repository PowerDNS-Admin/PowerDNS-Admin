import os
import logging
import sentry_sdk
from flask import Flask
from flask_mail import Mail
from flask_session import Session
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from werkzeug.middleware.proxy_fix import ProxyFix
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

    # HSTS
    if app.config.get('HSTS_ENABLED'):
        from flask_sslify import SSLify
        _sslify = SSLify(app)  # lgtm [py/unused-local-variable]

    # Load Flask-Session
    app.config['SESSION_TYPE'] = app.config.get('SESSION_TYPE')
    if 'SESSION_TYPE' in os.environ:
        app.config['SESSION_TYPE'] = os.environ.get('SESSION_TYPE')

    sess = Session(app)

    # create sessions table if using sqlalchemy backend
    if os.environ.get('SESSION_TYPE') == 'sqlalchemy':
        sess.app.session_interface.db.create_all()

    # SMTP
    app.mail = Mail(app)

    # Retrieve configuration from environment variables or app config
    sentry_dsn = os.environ.get("SENTRY_DSN", app.config.get("SENTRY_DSN"))
    sentry_enabled = str(os.environ.get("SENTRY_ENABLED", app.config.get("SENTRY_ENABLED", "false"))).strip().lower() == "true"

    if sentry_enabled and sentry_dsn:
        sentry_sdk.init(
            #TODO: Make this release dynamic
            #release="powerdns-admin@0.4.2",
            dsn=sentry_dsn,
            integrations = [
                FlaskIntegration(
                    #transaction_style="url",
                    http_methods_to_capture=("CONNECT", "DELETE", "GET", "PATCH", "POST", "PUT", "TRACE",),
                ),
                LoggingIntegration(),
                SqlalchemyIntegration(),
            ],
            debug=False,
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for tracing.
            traces_sample_rate=1.0,
        )
        app.logger.info("Sentry initialized successfully.")
    else:
        app.logger.info("Sentry not enabled or DSN missing.")
    
    # Load app's components
    assets.init_app(app)
    models.init_app(app)
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

    return app
