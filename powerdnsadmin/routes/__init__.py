from .base import login_manager, handle_bad_request, handle_unauthorized_access, handle_access_forbidden, handle_page_not_found, handle_internal_server_error

from .index import index_bp
from .user import user_bp
from .dashboard import dashboard_bp
from .domain import domain_bp
from .admin import admin_bp
from .api import api_bp


def init_app(app):
    login_manager.init_app(app)

    app.register_blueprint(index_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(domain_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    app.register_error_handler(400, handle_bad_request)
    app.register_error_handler(401, handle_unauthorized_access)
    app.register_error_handler(403, handle_access_forbidden)
    app.register_error_handler(404, handle_page_not_found)
    app.register_error_handler(500, handle_internal_server_error)
