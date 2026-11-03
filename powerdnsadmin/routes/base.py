import base64

from flask import g, render_template, url_for, redirect, session, request, current_app
from flask_login import LoginManager, logout_user
from flask_seasurf import SeaSurf
from flask_session_captcha import FlaskSessionCaptcha

from ..models.base import db
from ..models.user import User


captcha = FlaskSessionCaptcha()
csrf = SeaSurf()
login_manager = LoginManager()


def handle_bad_request(e):
    return render_template('errors/400.html', code=400, message=e), 400


def handle_unauthorized_access(e):
    throttled = getattr(g, 'auth_throttled', None)
    if throttled is not None:
        response = current_app.response_class(
            'Too many authentication attempts. Try again later.\n',
            status=429,
            mimetype='text/plain',
        )
        response.headers['Retry-After'] = str(throttled.retry_after)
        response.headers['Cache-Control'] = 'no-store'
        return response
    session['next'] = request.script_root + request.path
    return redirect(url_for('index.login'))


def handle_access_forbidden(e):
    expired_form = {
        'index.login': (
            'login.html',
            'Your login form expired. Please try again.',
            {
                'saml_enabled': current_app.config.get(
                    'SAML_ENABLED', False),
                'username': request.form.get('username', ''),
            },
        ),
        'index.register': (
            'register.html',
            'Your registration form expired. Please try again.',
            {
                'captcha_enable': current_app.config.get(
                    'CAPTCHA_ENABLE', False),
            },
        ),
    }.get(request.endpoint)

    if expired_form is not None and request.method == 'POST':
        # CSRF validation runs before either form's view. If a form is stale,
        # make sure an existing Flask-Login or SSO session cannot make the
        # rejected submission appear authenticated on the next request.
        logout_user()
        session.clear()
        session['_remember'] = 'clear'

        template, error, context = expired_form
        return render_template(
            template,
            error=error,
            **context,
        ), 403

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
        from ..lib.auth_throttle import ThrottleStoreUnavailable
        if isinstance(e, ThrottleStoreUnavailable):
            raise
        current_app.logger.error('Error: {0}'.format(e))
        return None


@login_manager.user_loader
def load_user(id):
    """
    This will be current_user.

    ``session_version`` is stored at login and bumped when the password
    changes. A session from before that change, or from before this check
    existed, does not match and the request stays anonymous.
    """
    user = db.session.get(User, int(id))
    if user is None:
        return None
    if session.get('session_version') != user.session_version:
        return None
    return user


@login_manager.request_loader
def login_via_authorization_header_or_remote_user(request):
    # Browser Basic authentication uses the same password, email, and TOTP
    # rules as the login form. It does not create a server session by itself.
    if request.headers.get('Authorization'):
        from ..decorators import accept_basic_credentials
        return accept_basic_credentials()

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
