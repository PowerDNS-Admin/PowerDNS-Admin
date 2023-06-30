import base64

from flask import render_template, url_for, redirect, session, request, current_app
from flask_login import LoginManager
from flask_seasurf import SeaSurf
from flask_session_captcha import FlaskSessionCaptcha

from ..models.user import User


captcha = FlaskSessionCaptcha()
csrf = SeaSurf()
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


def load_if_valid(user, method, src_ip, trust_user = False):
    try:
        auth = user.is_validate(method, src_ip, trust_user)
        if auth == False:
            return None
        else:
            # login_user(user, remember=False)
            return User.query.filter(User.id==user.id).first()
    except Exception as e:
        current_app.logger.error('Error: {0}'.format(e))
        return None


@login_manager.user_loader
def load_user(id):
    """
    This will be current_user
    """
    return User.query.get(int(id))


@login_manager.request_loader
def login_via_authorization_header_or_remote_user(request):
    # Try to login using Basic Authentication
    auth_header = request.headers.get('Authorization')
    if auth_header:

        if auth_header[:6] != "Basic ":
            return None

        auth_method = request.args.get('auth_method', 'LOCAL')
        auth_method = 'LDAP' if auth_method != 'LOCAL' else 'LOCAL'

        # Remove "Basic " from the header value
        auth_header = auth_header[6:]

        try:
            auth_header = str(base64.b64decode(auth_header), 'utf-8')
        except (UnicodeDecodeError, TypeError) as e:
            return None

        # NK: We use auth_components here as we don't know if we'll have a :, we split it maximum 1 times to grab the
        #     username, the rest of the string would be the password.
        auth_components = auth_header.split(':', maxsplit=1)

        # If we don't have two auth components (username, password), we can return
        if len(auth_components) != 2:
            return None

        (username, password) = auth_components

        user = User(username=username,
                    password=password,
                    plain_text_password=password)
        return load_if_valid(user, method=auth_method, src_ip=request.remote_addr)
    
    # Try login by checking a REMOTE_USER environment variable
    remote_user = request.remote_user
    if remote_user and current_app.config.get('REMOTE_USER_ENABLED'):
        session_remote_user = session.get('remote_user')
        
        # If we already validated a remote user against an authorization method
        # a local user should have been created in the database, so we force a 'LOCAL' auth_method
        auth_method = 'LOCAL' if session_remote_user else current_app.config.get('REMOTE_AUTH_METHOD', 'LDAP') 
        current_app.logger.debug(
            'REMOTE_USER environment variable found: attempting {0} authentication for username "{1}"'
            .format(auth_method, remote_user))
        user = User(username=remote_user.strip())
        valid_remote_user = load_if_valid(user, method=auth_method, src_ip=request.remote_addr, trust_user=True)
        
        if valid_remote_user:
            # If we were successful in authenticating a trusted remote user, store it in session
            session['remote_user'] = valid_remote_user.username

        return valid_remote_user

    return None
