from .base import (
    captcha, csrf, login_manager, handle_bad_request, handle_unauthorized_access,
    handle_access_forbidden, handle_page_not_found, handle_internal_server_error
)

from .index import index_bp
from .user import user_bp
from .dashboard import dashboard_bp
from .domain import domain_bp
from .admin import admin_bp
from .api import api_bp, apilist_bp
from .dyndns import dyndns_bp
from .swagger import swagger_bp
from .oauth import oauth_bp
from .saml import saml_bp


def init_app(app):
    from ..lib.api_audit import record_api_request

    @app.after_request
    def audit_api_request(response):
        record_api_request(response)
        return response

    @app.before_request
    def constrain_session():
        # Remember-me cookies are an HMAC of the user id under SECRET_KEY.
        # Flask-Login copies a valid one into the server session the first
        # time current_user is read. Mark it clear on every request so that
        # read cannot authenticate anyone.
        # The API blueprint does not apply session_timeout. Without this,
        # the session Flask-Login just created is saved for Flask's 31-day
        # default.
        from datetime import timedelta
        from flask import current_app, request, session
        from ..models.setting import Setting

        cookie_name = current_app.config.get(
            'REMEMBER_COOKIE_NAME', 'remember_token')
        if request.cookies.get(cookie_name):
            session['_remember'] = 'clear'

        try:
            minutes = int(Setting().get('session_timeout'))
        except (TypeError, ValueError):
            minutes = 10
        if minutes < 1:
            minutes = 10
        current_app.permanent_session_lifetime = timedelta(minutes=minutes)

    login_manager.init_app(app)
    csrf.init_app(app)
    captcha.init_app(app)

    app.register_blueprint(index_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(domain_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(apilist_bp)
    app.register_blueprint(dyndns_bp)
    app.register_blueprint(swagger_bp)
    app.register_blueprint(oauth_bp)
    app.register_blueprint(saml_bp)

    app.register_error_handler(400, handle_bad_request)
    app.register_error_handler(401, handle_unauthorized_access)
    app.register_error_handler(403, handle_access_forbidden)
    app.register_error_handler(404, handle_page_not_found)
    app.register_error_handler(500, handle_internal_server_error)
