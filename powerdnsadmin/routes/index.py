import os
import re
import json
import traceback
import datetime
import ipaddress
import base64
import string
from zxcvbn import zxcvbn
from distutils.util import strtobool
from yaml import Loader, load
from flask import Blueprint, render_template, make_response, url_for, current_app, g, session, request, redirect, abort
from flask_login import login_user, logout_user, login_required, current_user

from .base import captcha, csrf, login_manager
from ..lib import utils
from ..decorators import dyndns_login_required
from ..models.base import db
from ..models.user import User, Anonymous
from ..models.role import Role
from ..models.account import Account
from ..models.account_user import AccountUser
from ..models.domain import Domain
from ..models.domain_user import DomainUser
from ..models.domain_setting import DomainSetting
from ..models.record import Record
from ..models.setting import Setting
from ..models.history import History
from ..services.google import google_oauth
from ..services.github import github_oauth
from ..services.azure import azure_oauth
from ..services.oidc import oidc_oauth
from ..services.saml import SAML
from ..services.token import confirm_token
from ..services.email import send_account_verification

google = None
github = None
azure = None
oidc = None
saml = None

index_bp = Blueprint('index',
                     __name__,
                     template_folder='templates',
                     url_prefix='/')


@index_bp.before_app_first_request
def register_modules():
    global google
    global github
    global azure
    global oidc
    global saml
    google = google_oauth()
    github = github_oauth()
    azure = azure_oauth()
    oidc = oidc_oauth()
    saml = SAML()


@index_bp.before_request
def before_request():
    # Check if user is anonymous
    g.user = current_user
    login_manager.anonymous_user = Anonymous

    # Check site is in maintenance mode
    maintenance = Setting().get('maintenance')
    if maintenance and current_user.is_authenticated and current_user.role.name not in [
        'Administrator', 'Operator'
    ]:
        return render_template('maintenance.html')

    # Manage session timeout
    session.permanent = True
    current_app.permanent_session_lifetime = datetime.timedelta(
        minutes=int(Setting().get('session_timeout')))
    session.modified = True


@index_bp.route('/', methods=['GET'])
@login_required
def index():
    return redirect(url_for('dashboard.dashboard'))


@index_bp.route('/ping', methods=['GET'])
def ping():
    return make_response('ok')


@index_bp.route('/google/login')
def google_login():
    if not Setting().get('google_oauth_enabled') or google is None:
        current_app.logger.error(
            'Google OAuth is disabled or you have not yet reloaded the pda application after enabling.'
        )
        abort(400)
    else:
        use_ssl = current_app.config.get('SERVER_EXTERNAL_SSL')
        params = {'_external': True}
        if isinstance(use_ssl, bool):
            params['_scheme'] = 'https' if use_ssl else 'http'
        redirect_uri = url_for('google_authorized', **params)
        return google.authorize_redirect(redirect_uri)


@index_bp.route('/github/login')
def github_login():
    if not Setting().get('github_oauth_enabled') or github is None:
        current_app.logger.error(
            'Github OAuth is disabled or you have not yet reloaded the pda application after enabling.'
        )
        abort(400)
    else:
        use_ssl = current_app.config.get('SERVER_EXTERNAL_SSL')
        params = {'_external': True}
        if isinstance(use_ssl, bool):
            params['_scheme'] = 'https' if use_ssl else 'http'
        redirect_uri = url_for('github_authorized', **params)
        return github.authorize_redirect(redirect_uri)


@index_bp.route('/azure/login')
def azure_login():
    if not Setting().get('azure_oauth_enabled') or azure is None:
        current_app.logger.error(
            'Microsoft OAuth is disabled or you have not yet reloaded the pda application after enabling.'
        )
        abort(400)
    else:
        use_ssl = current_app.config.get('SERVER_EXTERNAL_SSL')
        params = {'_external': True}
        if isinstance(use_ssl, bool):
            params['_scheme'] = 'https' if use_ssl else 'http'
        redirect_uri = url_for('azure_authorized', **params)
        return azure.authorize_redirect(redirect_uri)


@index_bp.route('/oidc/login')
def oidc_login():
    if not Setting().get('oidc_oauth_enabled') or oidc is None:
        current_app.logger.error(
            'OIDC OAuth is disabled or you have not yet reloaded the pda application after enabling.'
        )
        abort(400)
    else:
        use_ssl = current_app.config.get('SERVER_EXTERNAL_SSL')
        params = {'_external': True}
        if isinstance(use_ssl, bool):
            params['_scheme'] = 'https' if use_ssl else 'http'
        redirect_uri = url_for('oidc_authorized', **params)
        return oidc.authorize_redirect(redirect_uri)


@index_bp.route('/login', methods=['GET', 'POST'])
def login():
    SAML_ENABLED = current_app.config.get('SAML_ENABLED', False)

    if g.user is not None and current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))

    if 'google_token' in session:
        user_data = json.loads(google.get('userinfo').text)
        google_first_name = user_data['given_name']
        google_last_name = user_data['family_name']
        google_email = user_data['email']
        user = User.query.filter_by(username=google_email).first()
        if user is None:
            user = User.query.filter_by(email=google_email).first()
        if not user:
            user = User(username=google_email,
                        firstname=google_first_name,
                        lastname=google_last_name,
                        plain_text_password=None,
                        email=google_email)

            result = user.create_local_user()
            if not result['status']:
                session.pop('google_token', None)
                return redirect(url_for('index.login'))

        session['user_id'] = user.id
        session['authentication_type'] = 'OAuth'
        return authenticate_user(user, 'Google OAuth')

    if 'github_token' in session:
        user_data = json.loads(github.get('user').text)
        github_username = user_data['login']
        github_first_name = user_data['name']
        github_last_name = ''
        github_email = user_data['email']

        # If the user's full name from GitHub contains at least two words, use the first word as the first name and
        # the rest as the last name.
        github_name_parts = github_first_name.split(' ')
        if len(github_name_parts) > 1:
            github_first_name = github_name_parts[0]
            github_last_name = ' '.join(github_name_parts[1:])

        user = User.query.filter_by(username=github_username).first()
        if user is None:
            user = User.query.filter_by(email=github_email).first()
        if not user:
            user = User(username=github_username,
                        plain_text_password=None,
                        firstname=github_first_name,
                        lastname=github_last_name,
                        email=github_email)

            result = user.create_local_user()
            if not result['status']:
                session.pop('github_token', None)
                return redirect(url_for('index.login'))

        session['user_id'] = user.id
        session['authentication_type'] = 'OAuth'
        return authenticate_user(user, 'Github OAuth')

    if 'azure_token' in session:
        azure_info = azure.get('me?$select=displayName,givenName,id,mail,surname,userPrincipalName').text
        current_app.logger.info('Azure login returned: ' + azure_info)
        user_data = json.loads(azure_info)

        azure_info = azure.post('me/getMemberGroups',
                                json={'securityEnabledOnly': False}).text
        current_app.logger.info('Azure groups returned: ' + azure_info)
        grouplookup = json.loads(azure_info)
        # Groups are in mygroups['value'] which is an array
        if "value" in grouplookup:
            mygroups = grouplookup["value"]
        else:
            mygroups = []

        azure_username = user_data["userPrincipalName"]
        azure_first_name = user_data["givenName"]
        azure_last_name = user_data["surname"]
        if "mail" in user_data:
            azure_email = user_data["mail"]
        else:
            azure_email = ""
        if not azure_email:
            azure_email = user_data["userPrincipalName"]

        # Handle foreign principals such as guest users
        azure_email = re.sub(r"#.*$", "", azure_email)
        azure_username = re.sub(r"#.*$", "", azure_username)

        user = User.query.filter_by(username=azure_username).first()
        if not user:
            user = User(username=azure_username,
                        plain_text_password=None,
                        firstname=azure_first_name,
                        lastname=azure_last_name,
                        email=azure_email)

            result = user.create_local_user()
            if not result['status']:
                current_app.logger.warning('Unable to create ' + azure_username + ' Reasoning: ' + result['msg'])
                session.pop('azure_token', None)
                # note: a redirect to login results in an endless loop, so render the login page instead
                return render_template('login.html',
                                       saml_enabled=SAML_ENABLED,
                                       error=('User ' + azure_username +
                                              ' cannot be created.'))

        session['user_id'] = user.id
        session['authentication_type'] = 'OAuth'

        # Handle group memberships, if defined
        if Setting().get('azure_sg_enabled'):
            if Setting().get('azure_admin_group') in mygroups:
                current_app.logger.info('Setting role for user ' +
                                        azure_username +
                                        ' to Administrator due to group membership')
                user.set_role("Administrator")
            else:
                if Setting().get('azure_operator_group') in mygroups:
                    current_app.logger.info('Setting role for user ' +
                                            azure_username +
                                            ' to Operator due to group membership')
                    user.set_role("Operator")
                else:
                    if Setting().get('azure_user_group') in mygroups:
                        current_app.logger.info('Setting role for user ' +
                                                azure_username +
                                                ' to User due to group membership')
                        user.set_role("User")
                    else:
                        current_app.logger.warning('User ' +
                                                   azure_username +
                                                   ' has no relevant group memberships')
                        session.pop('azure_token', None)
                        return render_template('login.html',
                                               saml_enabled=SAML_ENABLED,
                                               error=('User ' + azure_username +
                                                      ' is not in any authorised groups.'))

        # Handle account/group creation, if enabled
        if Setting().get('azure_group_accounts_enabled') and mygroups:
            current_app.logger.info('Azure group account sync enabled')
            name_value = Setting().get('azure_group_accounts_name')
            description_value = Setting().get('azure_group_accounts_description')
            select_values = name_value
            if description_value != '':
                select_values += ',' + description_value

            mygroups = get_azure_groups(
                'me/memberOf/microsoft.graph.group?$count=false&$securityEnabled=true&$select={}'.format(select_values))

            description_pattern = Setting().get('azure_group_accounts_description_re')
            pattern = Setting().get('azure_group_accounts_name_re')

            # Loop through users security groups
            for azure_group in mygroups:
                if name_value in azure_group:
                    group_name = azure_group[name_value]
                    group_description = ''
                    if description_value in azure_group:
                        group_description = azure_group[description_value]

                        # Do regex search if enabled for group description
                        if description_pattern != '':
                            current_app.logger.info('Matching group description {} against regex {}'.format(
                                group_description, description_pattern))
                            matches = re.match(
                                description_pattern, group_description)
                            if matches:
                                current_app.logger.info(
                                    'Group {} matched regexp'.format(group_description))
                                group_description = matches.group(1)
                            else:
                                # Regexp didn't match, continue to next iteration
                                continue

                    # Do regex search if enabled for group name
                    if pattern != '':
                        current_app.logger.info(
                            'Matching group name {} against regex {}'.format(group_name, pattern))
                        matches = re.match(pattern, group_name)
                        if matches:
                            current_app.logger.info(
                                'Group {} matched regexp'.format(group_name))
                            group_name = matches.group(1)
                        else:
                            # Regexp didn't match, continue to next iteration
                            continue

                    account = Account()
                    sanitized_group_name = Account.sanitize_name(group_name)
                    account_id = account.get_id_by_name(account_name=sanitized_group_name)

                    if account_id:
                        account = Account.query.get(account_id)
                        # check if user has permissions
                        account_users = account.get_user()
                        current_app.logger.info('Group: {} Users: {}'.format(
                            group_name,
                            account_users))
                        if user.id in account_users:
                            current_app.logger.info('User id {} is already in account {}'.format(
                                user.id, group_name))
                        else:
                            account.add_user(user)
                            history = History(msg='Update account {0}'.format(
                                account.name),
                                created_by='System')
                            history.add()
                            current_app.logger.info('User {} added to Account {}'.format(
                                user.username, account.name))
                    else:
                        account = Account(
                            name=sanitized_group_name,
                            description=group_description,
                            contact='',
                            mail=''
                        )
                        account.create_account()
                        history = History(msg='Create account {0}'.format(
                            account.name),
                            created_by='System')
                        history.add()

                        account.add_user(user)
                        history = History(msg='Update account {0}'.format(account.name),
                                          created_by='System')
                        history.add()
                    current_app.logger.warning('group info: {} '.format(account_id))

        return authenticate_user(user, 'Azure OAuth')

    if 'oidc_token' in session:
        user_data = oidc.userinfo()
        oidc_username = user_data[Setting().get('oidc_oauth_username')]
        oidc_first_name = user_data[Setting().get('oidc_oauth_firstname')]
        oidc_last_name = user_data[Setting().get('oidc_oauth_last_name')]
        oidc_email = user_data[Setting().get('oidc_oauth_email')]

        user = User.query.filter_by(username=oidc_username).first()
        if not user:
            user = User(username=oidc_username,
                        plain_text_password=None,
                        firstname=oidc_first_name,
                        lastname=oidc_last_name,
                        email=oidc_email)
            result = user.create_local_user()
        else:
            user.firstname = oidc_first_name
            user.lastname = oidc_last_name
            user.email = oidc_email
            user.plain_text_password = None
            result = user.update_local_user()

        if not result['status']:
            session.pop('oidc_token', None)
            return redirect(url_for('index.login'))

        # This checks if the account_name_property and account_description property were included in settings.
        if Setting().get('oidc_oauth_account_name_property') and Setting().get(
                'oidc_oauth_account_description_property'):

            # Gets the name_property and description_property.
            name_prop = Setting().get('oidc_oauth_account_name_property')
            desc_prop = Setting().get('oidc_oauth_account_description_property')

            account_to_add = []
            # If the name_property and desc_property exist in me (A variable that contains all the userinfo from the
            # IdP).
            if name_prop in user_data and desc_prop in user_data:
                accounts_name_prop = [user_data[name_prop]] if type(user_data[name_prop]) is not list else user_data[name_prop]
                accounts_desc_prop = [user_data[desc_prop]] if type(user_data[desc_prop]) is not list else user_data[desc_prop]

                # Run on all groups the user is in by the index num.
                for i in range(len(accounts_name_prop)):
                    description = ''
                    if i < len(accounts_desc_prop):
                        description = accounts_desc_prop[i]
                    account = handle_account(accounts_name_prop[i], description)

                    account_to_add.append(account)
                user_accounts = user.get_accounts()

                # Add accounts
                for account in account_to_add:
                    if account not in user_accounts:
                        account.add_user(user)

                # Remove accounts if the setting is enabled
                if Setting().get('delete_sso_accounts'):
                    for account in user_accounts:
                        if account not in account_to_add:
                            account.remove_user(user)

        session['user_id'] = user.id
        session['authentication_type'] = 'OAuth'
        return authenticate_user(user, 'OIDC OAuth')

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

        # check if user enabled OPT authentication
        if user.otp_secret:
            if otp_token and otp_token.isdigit():
                good_token = user.verify_totp(otp_token)
                if not good_token:
                    signin_history(user.username, auth_method, False)
                    return render_template('login.html',
                                           saml_enabled=SAML_ENABLED,
                                           error='Invalid credentials')
            else:
                return render_template('login.html',
                                       saml_enabled=SAML_ENABLED,
                                       error='Token required')

        if Setting().get('autoprovisioning') and auth_method != 'LOCAL':
            urn_value = Setting().get('urn_value')
            Entitlements = user.read_entitlements(Setting().get('autoprovisioning_attribute'))
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
                        current_app.logger.warning('Procceding to revoke every privilige from ' + user.username + '.')

        return authenticate_user(user, auth_method, remember_me)


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


def clear_session():
    session.pop('user_id', None)
    session.pop('github_token', None)
    session.pop('google_token', None)
    session.pop('azure_token', None)
    session.pop('oidc_token', None)
    session.pop('authentication_type', None)
    session.pop('remote_user', None)
    logout_user()


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


# Get a list of Azure security groups the user is a member of
def get_azure_groups(uri):
    azure_info = azure.get(uri).text
    current_app.logger.info('Azure groups returned: ' + azure_info)
    grouplookup = json.loads(azure_info)
    if "value" in grouplookup:
        mygroups = grouplookup["value"]
        # If "@odata.nextLink" exists in the results, we need to get more groups
        if "@odata.nextLink" in grouplookup:
            # The additional groups are added to the existing array
            mygroups.extend(get_azure_groups(grouplookup["@odata.nextLink"]))
    else:
        mygroups = []
    return mygroups


# Handle user login, write history and, if set, handle showing the register_otp QR code.
# if Setting for OTP on first login is enabled, and OTP field is also enabled,
# but user isn't using it yet, enable OTP, get QR code and display it, logging the user out.
def authenticate_user(user, authenticator, remember=False):
    login_user(user, remember=remember)
    signin_history(user.username, authenticator, True)
    if Setting().get('otp_force') and Setting().get('otp_field_enabled') and not user.otp_secret \
            and session['authentication_type'] not in ['OAuth']:
        user.update_profile(enable_otp=True)
        user_id = current_user.id
        prepare_welcome_user(user_id)
        return redirect(url_for('index.welcome'))
    return redirect(url_for('index.login'))


# Prepare user to enter /welcome screen, otherwise they won't have permission to do so
def prepare_welcome_user(user_id):
    logout_user()
    session['welcome_user_id'] = user_id


@index_bp.route('/logout')
def logout():
    if current_app.config.get(
            'SAML_ENABLED'
    ) and 'samlSessionIndex' in session and current_app.config.get('SAML_LOGOUT'):
        req = saml.prepare_flask_request(request)
        auth = saml.init_saml_auth(req)
        if current_app.config.get('SAML_LOGOUT_URL'):
            return redirect(
                auth.logout(
                    name_id_format=
                    "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                    return_to=current_app.config.get('SAML_LOGOUT_URL'),
                    session_index=session['samlSessionIndex'],
                    name_id=session['samlNameId']))
        return redirect(
            auth.logout(
                name_id_format=
                "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                session_index=session['samlSessionIndex'],
                name_id=session['samlNameId']))

    redirect_uri = url_for('index.login')
    oidc_logout = Setting().get('oidc_oauth_logout_url')

    if 'oidc_token' in session and oidc_logout:
        redirect_uri = "{}?redirect_uri={}".format(
            oidc_logout, url_for('index.login', _external=True))

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

    return redirect(redirect_uri)


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


@index_bp.route('/nic/checkip.html', methods=['GET', 'POST'])
@csrf.exempt
def dyndns_checkip():
    # This route covers the default ddclient 'web' setting for the checkip service
    return render_template('dyndns.html',
                           response=request.environ.get(
                               'HTTP_X_REAL_IP', request.remote_addr))


@index_bp.route('/nic/update', methods=['GET', 'POST'])
@csrf.exempt
@dyndns_login_required
def dyndns_update():
    # dyndns protocol response codes in use are:
    # good: update successful
    # nochg: IP address already set to update address
    # nohost: hostname does not exist for this user account
    # 911: server error
    # have to use 200 HTTP return codes because ddclient does not read the return string if the code is other than 200
    # reference: https://help.dyn.com/remote-access-api/perform-update/
    # reference: https://help.dyn.com/remote-access-api/return-codes/
    hostname = request.args.get('hostname')
    myip = request.args.get('myip')

    if not hostname:
        history = History(msg="DynDNS update: missing hostname parameter",
                          created_by=current_user.username)
        history.add()
        return render_template('dyndns.html', response='nohost'), 200

    try:
        if current_user.role.name in ['Administrator', 'Operator']:
            domains = Domain.query.all()
        else:
            # Get query for domain to which the user has access permission.
            # This includes direct domain permission AND permission through
            # account membership
            domains = db.session.query(Domain) \
                .outerjoin(DomainUser, Domain.id == DomainUser.domain_id) \
                .outerjoin(Account, Domain.account_id == Account.id) \
                .outerjoin(AccountUser, Account.id == AccountUser.account_id) \
                .filter(
                db.or_(
                    DomainUser.user_id == current_user.id,
                    AccountUser.user_id == current_user.id
                )).all()
    except Exception as e:
        current_app.logger.error('DynDNS Error: {0}'.format(e))
        current_app.logger.debug(traceback.format_exc())
        return render_template('dyndns.html', response='911'), 200

    domain = None
    domain_segments = hostname.split('.')
    for _index in range(len(domain_segments)):
        full_domain = '.'.join(domain_segments)
        potential_domain = Domain.query.filter(
            Domain.name == full_domain).first()
        if potential_domain in domains:
            domain = potential_domain
            break
        domain_segments.pop(0)

    if not domain:
        history = History(
            msg=
            "DynDNS update: attempted update of {0} but it does not exist for this user"
            .format(hostname),
            created_by=current_user.username)
        history.add()
        return render_template('dyndns.html', response='nohost'), 200

    myip_addr = []
    if myip:
        for address in myip.split(','):
            myip_addr += utils.validate_ipaddress(address)

    remote_addr = utils.validate_ipaddress(
        request.headers.get('X-Forwarded-For',
                            request.remote_addr).split(', ')[0])

    response = 'nochg'
    for ip in myip_addr or remote_addr:
        if isinstance(ip, ipaddress.IPv4Address):
            rtype = 'A'
        else:
            rtype = 'AAAA'

        r = Record(name=hostname, type=rtype)
        # Check if the user requested record exists within this domain
        if r.exists(domain.name) and r.is_allowed_edit():
            if r.data == str(ip):
                # Record content did not change, return 'nochg'
                history = History(
                    msg=
                    "DynDNS update: attempted update of {0} but record already up-to-date"
                    .format(hostname),
                    created_by=current_user.username,
                    domain_id=domain.id)
                history.add()
            else:
                oldip = r.data
                result = r.update(domain.name, str(ip))
                if result['status'] == 'ok':
                    history = History(
                        msg='DynDNS update: updated {} successfully'.format(hostname),
                        detail=json.dumps({
                            'domain': domain.name,
                            'record': hostname,
                            'type': rtype,
                            'old_value': oldip,
                            'new_value': str(ip)
                        }),
                        created_by=current_user.username,
                        domain_id=domain.id)
                    history.add()
                    response = 'good'
                else:
                    response = '911'
                    break
        elif r.is_allowed_edit():
            ondemand_creation = DomainSetting.query.filter(
                DomainSetting.domain == domain).filter(
                DomainSetting.setting == 'create_via_dyndns').first()
            if (ondemand_creation is not None) and (strtobool(
                    ondemand_creation.value) == True):

                # Build the rrset
                rrset_data = [{
                    "changetype": "REPLACE",
                    "name": hostname + '.',
                    "ttl": 3600,
                    "type": rtype,
                    "records": [{
                        "content": str(ip),
                        "disabled": False
                    }],
                    "comments": []
                }]

                # Format the rrset
                rrset = {"rrsets": rrset_data}
                result = Record().add(domain.name, rrset)
                if result['status'] == 'ok':
                    history = History(
                        msg=
                        'DynDNS update: created record {0} in zone {1} successfully'
                        .format(hostname, domain.name, str(ip)),
                        detail=json.dumps({
                            'domain': domain.name,
                            'record': hostname,
                            'value': str(ip)
                        }),
                        created_by=current_user.username,
                        domain_id=domain.id)
                    history.add()
                    response = 'good'
        else:
            history = History(
                msg=
                'DynDNS update: attempted update of {0} but it does not exist for this user'
                .format(hostname),
                created_by=current_user.username)
            history.add()

    return render_template('dyndns.html', response=response), 200


### START SAML AUTHENTICATION ###
@index_bp.route('/saml/login')
def saml_login():
    if not current_app.config.get('SAML_ENABLED', False):
        abort(400)
    from onelogin.saml2.utils import OneLogin_Saml2_Utils
    req = saml.prepare_flask_request(request)
    auth = saml.init_saml_auth(req)
    redirect_url = OneLogin_Saml2_Utils.get_self_url(req) + url_for(
        'index.saml_authorized')
    return redirect(auth.login(return_to=redirect_url))


@index_bp.route('/saml/metadata')
def saml_metadata():
    if not current_app.config.get('SAML_ENABLED', False):
        current_app.logger.error("SAML authentication is disabled.")
        abort(400)
    from onelogin.saml2.utils import OneLogin_Saml2_Utils
    req = saml.prepare_flask_request(request)
    auth = saml.init_saml_auth(req)
    settings = auth.get_settings()
    metadata = settings.get_sp_metadata()
    errors = settings.validate_metadata(metadata)

    if len(errors) == 0:
        resp = make_response(metadata, 200)
        resp.headers['Content-Type'] = 'text/xml'
    else:
        resp = make_response(errors.join(', '), 500)
    return resp


@index_bp.route('/saml/authorized', methods=['GET', 'POST'])
@csrf.exempt
def saml_authorized():
    errors = []
    if not current_app.config.get('SAML_ENABLED', False):
        current_app.logger.error("SAML authentication is disabled.")
        abort(400)
    from onelogin.saml2.utils import OneLogin_Saml2_Utils
    req = saml.prepare_flask_request(request)
    auth = saml.init_saml_auth(req)
    auth.process_response()
    current_app.logger.debug(auth.get_attributes())
    errors = auth.get_errors()
    if len(errors) == 0:
        session['samlUserdata'] = auth.get_attributes()
        session['samlNameId'] = auth.get_nameid()
        session['samlSessionIndex'] = auth.get_session_index()
        self_url = OneLogin_Saml2_Utils.get_self_url(req)
        self_url = self_url + req['script_name']
        if 'RelayState' in request.form and self_url != request.form[
            'RelayState']:
            return redirect(auth.redirect_to(request.form['RelayState']))
        if current_app.config.get('SAML_ATTRIBUTE_USERNAME', False):
            username = session['samlUserdata'][
                current_app.config['SAML_ATTRIBUTE_USERNAME']][0].lower()
        else:
            username = session['samlNameId'].lower()
        user = User.query.filter_by(username=username).first()
        if not user:
            # create user
            user = User(username=username,
                        plain_text_password=None,
                        email=session['samlNameId'])
            user.create_local_user()
        session['user_id'] = user.id
        email_attribute_name = current_app.config.get('SAML_ATTRIBUTE_EMAIL',
                                                      'email')
        givenname_attribute_name = current_app.config.get(
            'SAML_ATTRIBUTE_GIVENNAME', 'givenname')
        surname_attribute_name = current_app.config.get(
            'SAML_ATTRIBUTE_SURNAME', 'surname')
        name_attribute_name = current_app.config.get('SAML_ATTRIBUTE_NAME',
                                                     None)
        account_attribute_name = current_app.config.get(
            'SAML_ATTRIBUTE_ACCOUNT', None)
        admin_attribute_name = current_app.config.get('SAML_ATTRIBUTE_ADMIN',
                                                      None)
        group_attribute_name = current_app.config.get('SAML_ATTRIBUTE_GROUP',
                                                      None)
        admin_group_name = current_app.config.get('SAML_GROUP_ADMIN_NAME',
                                                  None)
        operator_group_name = current_app.config.get('SAML_GROUP_OPERATOR_NAME',
                                                     None)
        group_to_account_mapping = create_group_to_account_mapping()

        if email_attribute_name in session['samlUserdata']:
            user.email = session['samlUserdata'][email_attribute_name][
                0].lower()
        if givenname_attribute_name in session['samlUserdata']:
            user.firstname = session['samlUserdata'][givenname_attribute_name][
                0]
        if surname_attribute_name in session['samlUserdata']:
            user.lastname = session['samlUserdata'][surname_attribute_name][0]
        if name_attribute_name in session['samlUserdata']:
            name = session['samlUserdata'][name_attribute_name][0].split(' ')
            user.firstname = name[0]
            user.lastname = ' '.join(name[1:])

        if group_attribute_name:
            user_groups = session['samlUserdata'].get(group_attribute_name, [])
        else:
            user_groups = []
        if admin_attribute_name or group_attribute_name:
            user_accounts = set(user.get_accounts())
            saml_accounts = []
            for group_mapping in group_to_account_mapping:
                mapping = group_mapping.split('=')
                group = mapping[0]
                account_name = mapping[1]

                if group in user_groups:
                    account = handle_account(account_name)
                    saml_accounts.append(account)

            for account_name in session['samlUserdata'].get(
                    account_attribute_name, []):
                account = handle_account(account_name)
                saml_accounts.append(account)
            saml_accounts = set(saml_accounts)
            for account in saml_accounts - user_accounts:
                account.add_user(user)
                history = History(msg='Adding {0} to account {1}'.format(
                    user.username, account.name),
                    created_by='SAML Assertion')
                history.add()
            for account in user_accounts - saml_accounts:
                account.remove_user(user)
                history = History(msg='Removing {0} from account {1}'.format(
                    user.username, account.name),
                    created_by='SAML Assertion')
                history.add()
        if admin_attribute_name and 'true' in session['samlUserdata'].get(
                admin_attribute_name, []):
            uplift_to_admin(user)
        elif admin_group_name in user_groups:
            uplift_to_admin(user)
        elif operator_group_name in user_groups:
            uplift_to_operator(user)
        elif admin_attribute_name or group_attribute_name:
            if user.role.name != 'User':
                user.role_id = Role.query.filter_by(name='User').first().id
                history = History(msg='Demoting {0} to user'.format(
                    user.username),
                    created_by='SAML Assertion')
                history.add()
        user.plain_text_password = None
        user.update_profile()
        session['authentication_type'] = 'SAML'
        return authenticate_user(user, 'SAML')
    else:
        return render_template('errors/SAML.html', errors=errors)


def create_group_to_account_mapping():
    group_to_account_mapping_string = current_app.config.get(
        'SAML_GROUP_TO_ACCOUNT_MAPPING', None)
    if group_to_account_mapping_string and len(
            group_to_account_mapping_string.strip()) > 0:
        group_to_account_mapping = group_to_account_mapping_string.split(',')
    else:
        group_to_account_mapping = []
    return group_to_account_mapping


def handle_account(account_name, account_description=""):
    clean_name = Account.sanitize_name(account_name)
    account = Account.query.filter_by(name=clean_name).first()
    if not account:
        account = Account(name=clean_name,
                          description=account_description,
                          contact='',
                          mail='')
        account.create_account()
        history = History(msg='Account {0} created'.format(account.name),
                          created_by='OIDC/SAML Assertion')
        history.add()
    else:
        account.description = account_description
        account.update_account()
    return account


def uplift_to_admin(user):
    if user.role.name != 'Administrator':
        user.role_id = Role.query.filter_by(name='Administrator').first().id
        history = History(msg='Promoting {0} to administrator'.format(
            user.username),
            created_by='SAML Assertion')
        history.add()


def uplift_to_operator(user):
    if user.role.name != 'Operator':
        user.role_id = Role.query.filter_by(name='Operator').first().id
        history = History(msg='Promoting {0} to operator'.format(
            user.username),
            created_by='SAML Assertion')
        history.add()


@index_bp.route('/saml/sls')
def saml_logout():
    req = saml.prepare_flask_request(request)
    auth = saml.init_saml_auth(req)
    url = auth.process_slo()
    errors = auth.get_errors()
    if len(errors) == 0:
        clear_session()
        if url is not None:
            return redirect(url)
        elif current_app.config.get('SAML_LOGOUT_URL') is not None:
            return redirect(current_app.config.get('SAML_LOGOUT_URL'))
        else:
            return redirect(url_for('login'))
    else:
        return render_template('errors/SAML.html', errors=errors)


### END SAML AUTHENTICATION ###


@index_bp.route('/swagger', methods=['GET'])
def swagger_spec():
    try:
        spec_path = os.path.join(current_app.root_path, "swagger-spec.yaml")
        spec = open(spec_path, 'r')
        loaded_spec = load(spec.read(), Loader)
    except Exception as e:
        current_app.logger.error(
            'Cannot view swagger spec. Error: {0}'.format(e))
        current_app.logger.debug(traceback.format_exc())
        abort(500)

    resp = make_response(json.dumps(loaded_spec), 200)
    resp.headers['Content-Type'] = 'application/json'

    return resp
