import re
import traceback
import datetime
import base64
import string
from zxcvbn import zxcvbn
from flask import Blueprint, render_template, make_response, url_for, current_app, g, session, request, redirect, abort
from flask_login import login_required, current_user

from . import oauth as oauth_routes
from . import saml as saml_routes
from .auth_session import authenticate_user, signin_history, clear_session, prepare_welcome_user
from .base import captcha, login_manager
from ..lib import utils
from ..models.base import db
from ..models.user import User, Anonymous
from ..models.setting import Setting
from ..services.token import confirm_token
from ..services.email import send_account_verification

index_bp = Blueprint('index',
                     __name__,
                     template_folder='templates',
                     url_prefix='/')


@index_bp.before_request
def before_request():
    # Check if user is anonymous
    g.user = current_user
    login_manager.anonymous_user = Anonymous

    # Manage session timeout
    session.permanent = True
    current_app.permanent_session_lifetime = datetime.timedelta(minutes=int(Setting().get('session_timeout')))
    session.modified = True

    # Check site is in maintenance mode
    maintenance = Setting().get('maintenance')
    if maintenance and current_user.is_authenticated and current_user.role.name not in [
        'Administrator', 'Operator'
    ]:
        return render_template('maintenance.html')


@index_bp.route('/', methods=['GET'])
@login_required
def index():
    return redirect(url_for('dashboard.dashboard'))


@index_bp.route('/ping', methods=['GET'])
def ping():
    return make_response('ok')


@index_bp.route('/healthcheck', methods=['GET'])
def healthcheck():
    return make_response('ok')


@index_bp.route('/login', methods=['GET', 'POST'])
def login():
    SAML_ENABLED = current_app.config.get('SAML_ENABLED', False)

    if g.user is not None and current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))

    if request.args.get('restart'):
        clear_pending_totp()

    pending_totp_user_id = session.get('pending_totp_user_id')
    if pending_totp_user_id is not None:
        pending_totp_user = db.session.get(User, pending_totp_user_id)
        if pending_totp_user is None or not pending_totp_user.otp_secret:
            clear_pending_totp()
            if request.method == 'POST':
                return redirect(url_for('index.login'))
        elif request.method == 'GET':
            return render_template('login.html',
                                   saml_enabled=SAML_ENABLED,
                                   otp_required=True,
                                   username=pending_totp_user.username)
        else:
            otp_token = request.form.get('otptoken', '')
            auth_method = session.get('pending_totp_auth_method', 'LOCAL')
            remember_me = session.get('pending_totp_remember', False)
            if not otp_token.isdigit() or not pending_totp_user.verify_totp(otp_token):
                signin_history(pending_totp_user.username, auth_method, False)
                return render_template('login.html',
                                       saml_enabled=SAML_ENABLED,
                                       otp_required=True,
                                       username=pending_totp_user.username,
                                       error='Invalid credentials')

            clear_pending_totp()
            apply_autoprovisioning(pending_totp_user, auth_method)
            return authenticate_user(pending_totp_user, auth_method,
                                     remember_me)

    if request.method == 'GET':
        return render_template('login.html', saml_enabled=SAML_ENABLED)
    elif request.method == 'POST':
        # process Local-DB authentication
        username = request.form['username']
        password = request.form['password']
        otp_token = request.form.get('otptoken')
        auth_method = request.form.get('auth_method', 'LOCAL')
        session[
            'authentication_type'] = 'LDAP' if auth_method != 'LOCAL' else 'LOCAL'
        remember_me = True if 'remember' in request.form else False

        if auth_method == 'LOCAL' and not Setting().get('local_db_enabled'):
            return render_template(
                'login.html',
                saml_enabled=SAML_ENABLED,
                error='Local authentication is disabled')

        user = User(username=username,
                    password=password,
                    plain_text_password=password)

        try:
            if Setting().get('verify_user_email') and user.email and not user.confirmed:
                return render_template(
                    'login.html',
                    saml_enabled=SAML_ENABLED,
                    error='Please confirm your email address first')

            auth = user.is_validate(method=auth_method,
                                    src_ip=request.remote_addr)
            if auth == False:
                signin_history(user.username, auth_method, False)
                return render_template('login.html',
                                       saml_enabled=SAML_ENABLED,
                                       error='Invalid credentials')
        except Exception as e:
            current_app.logger.error(
                "Cannot authenticate user. Error: {}".format(e))
            current_app.logger.debug(traceback.format_exc())
            return render_template('login.html',
                                   saml_enabled=SAML_ENABLED,
                                   error=e)

        # Only prompt for OTP after the supplied credentials identify a user
        # who has TOTP configured. This avoids showing an irrelevant OTP field
        # to every user on the initial sign-in form.
        if user.otp_secret:
            if otp_token and otp_token.isdigit():
                good_token = user.verify_totp(otp_token)
                if not good_token:
                    signin_history(user.username, auth_method, False)
                    return render_template('login.html',
                                           saml_enabled=SAML_ENABLED,
                                           error='Invalid credentials')
            else:
                session['pending_totp_user_id'] = user.id
                session['pending_totp_auth_method'] = auth_method
                session['pending_totp_remember'] = remember_me
                return render_template('login.html',
                                       saml_enabled=SAML_ENABLED,
                                       otp_required=True,
                                       username=user.username)

        apply_autoprovisioning(user, auth_method)

        return authenticate_user(user, auth_method, remember_me)


def clear_pending_totp():
    session.pop('pending_totp_user_id', None)
    session.pop('pending_totp_auth_method', None)
    session.pop('pending_totp_remember', None)


def apply_autoprovisioning(user, auth_method):
    if not Setting().get('autoprovisioning') or auth_method == 'LOCAL':
        return

    urn_value = Setting().get('urn_value')
    Entitlements = user.read_entitlements(
        Setting().get('autoprovisioning_attribute'))
    if len(Entitlements) == 0 and Setting().get('purge'):
        user.set_role("User")
        user.revoke_privilege(True)
    elif len(Entitlements) != 0:
        if checkForPDAEntries(Entitlements, urn_value):
            user.updateUser(Entitlements)
        else:
            current_app.logger.warning(
                'Not a single powerdns-admin record was found, possibly a typo in the prefix')
            if Setting().get('purge'):
                user.set_role("User")
                user.revoke_privilege(True)
                current_app.logger.warning(
                    'Procceding to revoke every privilige from ' +
                    user.username + '.')


def checkForPDAEntries(Entitlements, urn_value):
    """
    Run through every record located in the ldap attribute given and determine if there are any valid powerdns-admin records
    """
    urnArguments = [x.lower() for x in urn_value.split(':')]
    for Entitlement in Entitlements:
        entArguments = Entitlement.split(':powerdns-admin')
        entArguments = [x.lower() for x in entArguments[0].split(':')]
        if (entArguments == urnArguments):
            return True
    return False


@index_bp.route('/logout')
def logout():
    if current_app.config.get(
            'SAML_ENABLED'
    ) and 'samlSessionIndex' in session and current_app.config.get('SAML_LOGOUT'):
        return saml_routes.start_idp_logout()

    oidc_logout = None
    if 'oidc_token' in session:
        oidc_logout = oauth_routes.prepare_oidc_logout()

    # Clean cookies and flask session
    clear_session()

    # If remote user authentication is enabled and a logout URL is configured for it,
    # redirect users to that instead
    remote_user_logout_url = current_app.config.get('REMOTE_USER_LOGOUT_URL')
    if current_app.config.get('REMOTE_USER_ENABLED') and remote_user_logout_url:
        current_app.logger.debug(
            'Redirecting remote user "{0}" to logout URL {1}'
            .format(current_user.username, remote_user_logout_url))
        # Warning: if REMOTE_USER environment variable is still set and not cleared by
        # some external module, not defining a custom logout URL will trigger a loop
        # that will just log the user back in right after logging out
        res = make_response(redirect(remote_user_logout_url.strip()))

        # Remove any custom cookies the remote authentication mechanism may use
        # (e.g.: MOD_AUTH_CAS and MOD_AUTH_CAS_S)
        remote_cookies = current_app.config.get('REMOTE_USER_COOKIES')
        for r_cookie_name in utils.ensure_list(remote_cookies):
            res.delete_cookie(r_cookie_name)

        return res

    if oidc_logout:
        oidc_response = oauth_routes.start_oidc_logout(*oidc_logout)
        if oidc_response is not None:
            return oidc_response

    return redirect(url_for('index.login'))


def password_policy_check(user, password):
    def check_policy(chars, user_password, setting):
        setting_as_int = int(Setting().get(setting))
        test_string = user_password
        for c in chars:
            test_string = test_string.replace(c, '')
        return (setting_as_int, len(user_password) - len(test_string))

    def matches_policy(item, policy_fails):
        return "*" if item in policy_fails else ""

    policy = []
    policy_fails = {}

    # If either policy is enabled check basics first ... this is obvious!
    if Setting().get('pwd_enforce_characters') or Setting().get('pwd_enforce_complexity'):
        # Cannot contain username
        if user.username in password:
            policy_fails["username"] = True
        policy.append(f"{matches_policy('username', policy_fails)}cannot contain username")

        # Cannot contain password
        if user.firstname in password:
            policy_fails["firstname"] = True
        policy.append(f"{matches_policy('firstname', policy_fails)}cannot contain firstname")

        # Cannot contain lastname
        if user.lastname in password:
            policy_fails["lastname"] = True
        policy.append(f"{matches_policy('lastname', policy_fails)}cannot contain lastname")

        # Cannot contain email
        if user.email in password:
            policy_fails["email"] = True
        policy.append(f"{matches_policy('email', policy_fails)}cannot contain email")

    # Check if we're enforcing character requirements
    if Setting().get('pwd_enforce_characters'):
        # Length
        pwd_min_len_setting = int(Setting().get('pwd_min_len'))
        pwd_len = len(password)
        if pwd_len < pwd_min_len_setting:
            policy_fails["length"] = True
        policy.append(f"{matches_policy('length', policy_fails)}length={pwd_len}/{pwd_min_len_setting}")
        # Digits
        (pwd_min_digits_setting, pwd_digits) = check_policy(string.digits, password, 'pwd_min_digits')
        if pwd_digits < pwd_min_digits_setting:
            policy_fails["digits"] = True
        policy.append(f"{matches_policy('digits', policy_fails)}digits={pwd_digits}/{pwd_min_digits_setting}")
        # Lowercase
        (pwd_min_lowercase_setting, pwd_lowercase) = check_policy(string.digits, password, 'pwd_min_lowercase')
        if pwd_lowercase < pwd_min_lowercase_setting:
            policy_fails["lowercase"] = True
        policy.append(
            f"{matches_policy('lowercase', policy_fails)}lowercase={pwd_lowercase}/{pwd_min_lowercase_setting}")
        # Uppercase
        (pwd_min_uppercase_setting, pwd_uppercase) = check_policy(string.digits, password, 'pwd_min_uppercase')
        if pwd_uppercase < pwd_min_uppercase_setting:
            policy_fails["uppercase"] = True
        policy.append(
            f"{matches_policy('uppercase', policy_fails)}uppercase={pwd_uppercase}/{pwd_min_uppercase_setting}")
        # Special
        (pwd_min_special_setting, pwd_special) = check_policy(string.digits, password, 'pwd_min_special')
        if pwd_special < pwd_min_special_setting:
            policy_fails["special"] = True
        policy.append(f"{matches_policy('special', policy_fails)}special={pwd_special}/{pwd_min_special_setting}")

    if Setting().get('pwd_enforce_complexity'):
        # Complexity checking
        zxcvbn_inputs = []
        for input in (user.firstname, user.lastname, user.username, user.email):
            if len(input):
                zxcvbn_inputs.append(input)

        result = zxcvbn(password, user_inputs=zxcvbn_inputs)
        pwd_min_complexity_setting = int(Setting().get('pwd_min_complexity'))
        pwd_complexity = result['guesses_log10']
        if pwd_complexity < pwd_min_complexity_setting:
            policy_fails["complexity"] = True
        policy.append(
            f"{matches_policy('complexity', policy_fails)}complexity={pwd_complexity:.0f}/{pwd_min_complexity_setting}")

    policy_str = {"password": f"Fails policy: {', '.join(policy)}. Items prefixed with '*' failed."}

    # NK: the first item in the tuple indicates a PASS, so, we check for any True's and negate that
    return (not any(policy_fails.values()), policy_str)


@index_bp.route('/register', methods=['GET', 'POST'])
def register():
    CAPTCHA_ENABLE = current_app.config.get('CAPTCHA_ENABLE')
    if Setting().get('signup_enabled'):
        if current_user.is_authenticated:
            return redirect(url_for('index.index'))
        if request.method == 'GET':
            return render_template('register.html', captcha_enable=CAPTCHA_ENABLE)
        elif request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            firstname = request.form.get('firstname', '').strip()
            lastname = request.form.get('lastname', '').strip()
            email = request.form.get('email', '').strip()
            rpassword = request.form.get('rpassword', '')

            is_valid_email = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

            error_messages = {}
            if not firstname:
                error_messages['firstname'] = 'First Name is required'
            if not lastname:
                error_messages['lastname'] = 'Last Name is required'
            if not username:
                error_messages['username'] = 'Username is required'
            if not password:
                error_messages['password'] = 'Password is required'
            if not rpassword:
                error_messages['rpassword'] = 'Password confirmation is required'
            if not email:
                error_messages['email'] = 'Email is required'
            if not is_valid_email.match(email):
                error_messages['email'] = 'Invalid email address'
            if password != rpassword:
                error_messages['password'] = 'Password confirmation does not match'
                error_messages['rpassword'] = 'Password confirmation does not match'

            if not captcha.validate():
                return render_template(
                    'register.html', error='Invalid CAPTCHA answer', error_messages=error_messages,
                    captcha_enable=CAPTCHA_ENABLE)

            if error_messages:
                return render_template('register.html', error_messages=error_messages, captcha_enable=CAPTCHA_ENABLE)

            user = User(username=username,
                        plain_text_password=password,
                        firstname=firstname,
                        lastname=lastname,
                        email=email
                        )

            (password_policy_pass, password_policy) = password_policy_check(user, password)
            if not password_policy_pass:
                return render_template('register.html', error_messages=password_policy, captcha_enable=CAPTCHA_ENABLE)

            try:
                result = user.create_local_user()
                if result and result['status']:
                    if Setting().get('verify_user_email'):
                        send_account_verification(email)
                    if Setting().get('otp_force') and Setting().get('otp_field_enabled'):
                        user.update_profile(enable_otp=True)
                        prepare_welcome_user(user.id)
                        return redirect(url_for('index.welcome'))
                    else:
                        return redirect(url_for('index.login'))
                else:
                    return render_template('register.html',
                                           error=result['msg'], captcha_enable=CAPTCHA_ENABLE)
            except Exception as e:
                db.session.rollback()
                current_app.logger.exception(
                    'Unable to register local user %r', username)
                return render_template('register.html', error=e, captcha_enable=CAPTCHA_ENABLE)
        else:
            return render_template('errors/404.html'), 404


# Show welcome page on first login if otp_force is enabled
@index_bp.route('/welcome', methods=['GET', 'POST'])
def welcome():
    if 'welcome_user_id' not in session:
        return redirect(url_for('index.index'))

    user = User(id=session['welcome_user_id'])
    encoded_img_data = base64.b64encode(user.get_qrcode_value())

    if request.method == 'GET':
        return render_template('register_otp.html', qrcode_image=encoded_img_data.decode(), user=user)
    elif request.method == 'POST':
        otp_token = request.form.get('otptoken', '')
        if otp_token and otp_token.isdigit():
            good_token = user.verify_totp(otp_token)
            if not good_token:
                return render_template('register_otp.html', qrcode_image=encoded_img_data.decode(), user=user,
                                       error="Invalid token")
        else:
            return render_template('register_otp.html', qrcode_image=encoded_img_data.decode(), user=user,
                                   error="Token required")
        session.pop('welcome_user_id')
        return redirect(url_for('index.index'))


@index_bp.route('/confirm/<token>', methods=['GET'])
def confirm_email(token):
    email = confirm_token(token)
    if not email:
        # Cannot confirm email
        return render_template('email_confirmation.html', status=0)

    user = User.query.filter_by(email=email).first_or_404()
    if user.confirmed:
        # Already confirmed
        current_app.logger.info(
            "User email {} already confirmed".format(email))
        return render_template('email_confirmation.html', status=2)
    else:
        # Confirm email is valid
        user.update_confirmed(confirmed=1)
        current_app.logger.info(
            "User email {} confirmed successfully".format(email))
        return render_template('email_confirmation.html', status=1)


@index_bp.route('/resend-confirmation-email', methods=['GET', 'POST'])
def resend_confirmation_email():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    if request.method == 'GET':
        return render_template('resend_confirmation_email.html')
    elif request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter(User.email == email).first()
        if not user:
            # Email not found
            status = 0
        elif user.confirmed:
            # Email already confirmed
            status = 1
        else:
            # Send new confirmed email
            send_account_verification(user.email)
            status = 2

        return render_template('resend_confirmation_email.html', status=status)
