import base64
from flask import render_template, url_for, redirect, session, request, current_app
from flask_login import LoginManager

from ..models.user import User

login_manager = LoginManager()


def handle_bad_request(e):
    return render_template('errors/400.html', code=400, message=e), 400


def handle_unauthorized_access(e):
    session['next'] = request.script_root + request.path
    return redirect(url_for('index.login'))


def handle_access_forbidden(e):
    return render_template('errors/403.html', code=403, message=e), 403


def handle_page_not_found(e):
    return render_template('errors/404.html', code=404, message=e), 404


def handle_internal_server_error(e):
    return render_template('errors/500.html', code=500, message=e), 500


@login_manager.user_loader
def load_user(id):
    """
    This will be current_user
    """
    return User.query.get(int(id))


@login_manager.request_loader
def login_via_authorization_header(request):
    auth_header = request.headers.get('Authorization')
    if auth_header:
        auth_header = auth_header.replace('Basic ', '', 1)
        try:
            auth_header = str(base64.b64decode(auth_header), 'utf-8')
            username, password = auth_header.split(":")
        except TypeError as e:
            return None
        user = User(username=username,
                    password=password,
                    plain_text_password=password)
        try:
            auth_method = request.args.get('auth_method', 'LOCAL')
            auth_method = 'LDAP' if auth_method != 'LOCAL' else 'LOCAL'
            auth = user.is_validate(method=auth_method,
                                    src_ip=request.remote_addr)
            if auth == False:
                return None
            else:
                # login_user(user, remember=False)
                return User.query.filter(User.id==user.id).first()
        except Exception as e:
            current_app.logger.error('Error: {0}'.format(e))
            return None
    return None
