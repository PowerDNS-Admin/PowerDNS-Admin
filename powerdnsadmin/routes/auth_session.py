"""Post-authentication session lifecycle helpers.

These are shared by every auth mechanism (local, LDAP, OAuth, OIDC, SAML) once
a user's identity has been established, so they live here rather than in any
one provider's route module.
"""
import json
from flask import current_app, session, redirect, url_for, request
from flask_login import login_user, logout_user, current_user

from ..models.setting import Setting
from ..models.history import History


_AUTH_SESSION_KEYS = (
    'user_id',
    'github_token',
    'google_token',
    'azure_token',
    'oidc_token',
    'authentication_type',
    'remote_user',
    'github_oauthredir',
    'google_oauthredir',
    'azure_oauthredir',
    'oidc_oauthredir',
    'samlUserdata',
    'samlNameId',
    'samlSessionIndex',
    'pending_totp_user_id',
    'pending_totp_auth_method',
    'pending_totp_remember',
    'welcome_user_id',
    'next',
)


def signin_history(username, authenticator, success):
    # Get user ip address
    if request.headers.getlist("X-Forwarded-For"):
        request_ip = request.headers.getlist("X-Forwarded-For")[0]
        request_ip = request_ip.split(',')[0]
    else:
        request_ip = request.remote_addr

    # Write log
    if success:
        str_success = 'succeeded'
        current_app.logger.info(
            "User {} authenticated successfully via {} from {}".format(
                username, authenticator, request_ip))
    else:
        str_success = 'failed'
        current_app.logger.warning(
            "User {} failed to authenticate via {} from {}".format(
                username, authenticator, request_ip))

    # Write history
    History(msg='User {} authentication {}'.format(username, str_success),
            detail=json.dumps({
                'username': username,
                'authenticator': authenticator,
                'ip_address': request_ip,
                'success': 1 if success else 0
            }),
            created_by='System').add()


# Prepare user to enter /welcome screen, otherwise they won't have permission to do so
def prepare_welcome_user(user_id):
    logout_user()
    session['welcome_user_id'] = user_id


# Handle user login, write history and, if set, handle showing the register_otp QR code.
# if Setting for OTP on first login is enabled, and OTP field is also enabled,
# but user isn't using it yet, enable OTP, get QR code and display it, logging the user out.
def authenticate_user(user, authenticator, remember=False):
    login_user(user, remember=remember)
    # Do not keep using the anonymous/pre-authentication server-side session
    # after the user's identity has changed. Besides preventing session
    # fixation, this gives the authenticated session its own fresh expiry
    # instead of inheriting the lifetime of a login page that may have been
    # open for a long time.
    current_app.session_interface.regenerate(session)
    session.permanent = True
    session.modified = True
    signin_history(user.username, authenticator, True)
    if Setting().get('otp_force') and Setting().get('otp_field_enabled') and not user.otp_secret \
            and session['authentication_type'] not in ['OAuth']:
        user.update_profile(enable_otp=True)
        user_id = current_user.id
        prepare_welcome_user(user_id)
        return redirect(url_for('index.welcome'))
    return redirect(url_for('index.login'))


def clear_session():
    """Remove authentication state without discarding unrelated session data.

    Flask-Login owns its internal session keys, so let ``logout_user`` clear
    those and set the remember-cookie cleanup marker. Authlib state keys are
    dynamic and therefore need prefix-based removal.
    """
    for key in _AUTH_SESSION_KEYS:
        session.pop(key, None)
    for key in tuple(session):
        if key.startswith('_state_'):
            session.pop(key, None)
    logout_user()
