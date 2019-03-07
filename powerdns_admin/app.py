import sys
import os
from werkzeug.contrib.fixers import ProxyFix
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate

# from authlib.flask.client import OAuth as AuthlibOAuth
from flask_seasurf import SeaSurf
from powerdns_admin.assets import assets
from powerdns_admin.lib.log import logger
from powerdns_admin.lib import certutil
from powerdns_admin.models import db
from powerdns_admin.lib.utils import display_record_name, display_master_name
from powerdns_admin.lib.utils import display_time, email_to_gravatar_url
from powerdns_admin.lib.utils import display_setting_state

csrf = SeaSurf()
login_manager = LoginManager()

from powerdns_admin.blueprints.api import api_blueprint
from powerdns_admin.blueprints.views import views_blueprint


def create_app():
    environment = os.environ.get("ENVIRONMENT").lower()
    app = Flask(__name__)

    try:
        app.config.from_object("configs.{}".format(environment))
    except Exception as e:
        sys.stderr.write("ERROR: {0!s}".format(e))
        exit(1)

    app.config["ENVIRONMENT"] = environment
    app.wsgi_app = ProxyFix(app.wsgi_app)

    logger("powerdns-admin", app.config["LOG_LEVEL"], app.config["LOG_FILE"]).config()

    assets.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    db.init_app(app)
    Migrate(app, db)  # flask-migrate

    # FILTERS
    app.jinja_env.filters["display_record_name"] = display_record_name
    app.jinja_env.filters["display_master_name"] = display_master_name
    app.jinja_env.filters["display_second_to_time"] = display_time
    app.jinja_env.filters["email_to_gravatar_url"] = email_to_gravatar_url
    app.jinja_env.filters["display_setting_state"] = display_setting_state

    if app.config.get("SAML_ENABLED") and app.config.get("SAML_ENCRYPT"):
        if not certutil.check_certificate():
            certutil.create_self_signed_cert()

    app.register_blueprint(api_blueprint, url_prefix="/api/v1")
    app.register_blueprint(views_blueprint)

    return app


app = create_app()
