import os
import re
import json
import traceback
import datetime
import ipaddress
from distutils.util import strtobool
from yaml import Loader, load
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from flask import Blueprint, render_template, make_response, url_for, current_app, g, session, request, redirect, abort
from flask_login import login_user, logout_user, login_required, current_user

from .base import login_manager
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
@login_required
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
        redirect_uri = url_for('google_authorized', _external=True)
        return google.authorize_redirect(redirect_uri)


@index_bp.route('/github/login')
def github_login():
    if not Setting().get('github_oauth_enabled') or github is None:
        current_app.logger.error(
            'Github OAuth is disabled or you have not yet reloaded the pda application after enabling.'
        )
        abort(400)
    else:
        redirect_uri = url_for('github_authorized', _external=True)
        return github.authorize_redirect(redirect_uri)


@index_bp.route('/azure/login')
def azure_login():
    if not Setting().get('azure_oauth_enabled') or azure is None:
        current_app.logger.error(
            'Microsoft OAuth is disabled or you have not yet reloaded the pda application after enabling.'
        )
        abort(400)
    else:
        redirect_uri = url_for('azure_authorized',
                               _external=True,
                               _scheme='https')
        return azure.authorize_redirect(redirect_uri)


@index_bp.route('/oidc/login')
def oidc_login():
    if not Setting().get('oidc_oauth_enabled') or oidc is None:
        current_app.logger.error(
            'OIDC OAuth is disabled or you have not yet reloaded the pda application after enabling.'
        )
        abort(400)
    else:
        redirect_uri = url_for('oidc_authorized', _external=True)
        return oidc.authorize_redirect(redirect_uri)


@index_bp.route('/login', methods=['GET', 'POST'])
def login():
    SAML_ENABLED = current_app.config.get('SAML_ENABLED')

    if g.user is not None and current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))

    if 'google_token' in session:
        user_data = json.loads(google.get('userinfo').text)
        first_name = user_data['given_name']
        surname = user_data['family_name']
        email = user_data['email']
        user = User.query.filter_by(username=email).first()
        if user is None:
            user = User.query.filter_by(email=email).first()
        if not user:
            user = User(username=email,
                        firstname=first_name,
                        lastname=surname,
                        plain_text_password=None,
                        email=email)

            result = user.create_local_user()
            if not result['status']:
                session.pop('google_token', None)
                return redirect(url_for('index.login'))

        session['user_id'] = user.id
        login_user(user, remember=False)
        session['authentication_type'] = 'OAuth'
        signin_history(user.username, 'Google OAuth', True)
        return redirect(url_for('index.index'))

    if 'github_token' in session:
        me = json.loads(github.get('user').text)
        github_username = me['login']
        github_name = me['name']
        github_email = me['email']

        user = User.query.filter_by(username=github_username).first()
        if user is None:
            user = User.query.filter_by(email=github_email).first()
        if not user:
            user = User(username=github_username,
                        plain_text_password=None,
                        firstname=github_name,
                        lastname='',
                        email=github_email)

            result = user.create_local_user()
            if not result['status']:
                session.pop('github_token', None)
                return redirect(url_for('index.login'))

        session['user_id'] = user.id
        session['authentication_type'] = 'OAuth'
        login_user(user, remember=False)
        signin_history(user.username, 'Github OAuth', True)
        return redirect(url_for('index.index'))

    if 'azure_token' in session:
        azure_info = azure.get('me?$select=displayName,givenName,id,mail,surname,userPrincipalName,preferredName').text
        current_app.logger.info('Azure login returned: '+azure_info)
        me = json.loads(azure_info)

        azure_info = azure.post('me/getMemberGroups',
                                json={'securityEnabledOnly': False}).text
        current_app.logger.info('Azure groups returned: ' + azure_info)
        grouplookup = json.loads(azure_info)
        # Groups are in mygroups['value'] which is an array
        if "value" in grouplookup:
            mygroups = grouplookup["value"]
        else:
            mygroups = []

        azure_username = me["userPrincipalName"]
        azure_givenname = me["givenName"]
        azure_familyname = me["surname"]
        if "email" in me:
            azure_email = me["email"]
        else:
            azure_email = ""
        if not azure_email:
            azure_email = me["userPrincipalName"]

        # Handle foreign principals such as guest users
        azure_email = re.sub(r"#.*$", "", azure_email)
        azure_username = re.sub(r"#.*$", "", azure_username)

        user = User.query.filter_by(username=azure_username).first()
        if not user:
            user = User(username=azure_username,
                        plain_text_password=None,
                        firstname=azure_givenname,
                        lastname=azure_familyname,
                        email=azure_email)

            result = user.create_local_user()
            if not result['status']:
                current_app.logger.warning('Unable to create ' + azure_username)
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
                    azure_username  +
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

        login_user(user, remember=False)
        signin_history(user.username, 'Azure OAuth', True)
        return redirect(url_for('index.index'))

    if 'oidc_token' in session:
        me = json.loads(oidc.get('userinfo').text)
        oidc_username = me["preferred_username"]
        oidc_givenname = me["name"]
        oidc_familyname = ""
        oidc_email = me["email"]

        user = User.query.filter_by(username=oidc_username).first()
        if not user:
            user = User(username=oidc_username,
                        plain_text_password=None,
                        firstname=oidc_givenname,
                        lastname=oidc_familyname,
                        email=oidc_email)

            result = user.create_local_user()
            if not result['status']:
                session.pop('oidc_token', None)
                return redirect(url_for('index.login'))

        session['user_id'] = user.id
        session['authentication_type'] = 'OAuth'
        login_user(user, remember=False)
        signin_history(user.username, 'OIDC OAuth', True)
        return redirect(url_for('index.index'))

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
                signin_history(user.username, 'LOCAL', False)
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
                    signin_history(user.username, 'LOCAL', False)
                    return render_template('login.html',
                                           saml_enabled=SAML_ENABLED,
                                           error='Invalid credentials')
            else:
                return render_template('login.html',
                                       saml_enabled=SAML_ENABLED,
                                       error='Token required')

        login_user(user, remember=remember_me)
        signin_history(user.username, 'LOCAL', True)
        return redirect(session.get('next', url_for('index.index')))


def clear_session():
    session.pop('user_id', None)
    session.pop('github_token', None)
    session.pop('google_token', None)
    session.pop('authentication_type', None)
    session.clear()
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
            detail=str({
                "username": username,
                "authenticator": authenticator,
                "ip_address": request_ip,
                "success": 1 if success else 0
            }),
            created_by='System').add()


@index_bp.route('/logout')
def logout():
    if current_app.config.get(
            'SAML_ENABLED'
    ) and 'samlSessionIndex' in session and current_app.config.get(
            'SAML_LOGOUT'):
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
    clear_session()
    return redirect(url_for('index.login'))


@index_bp.route('/register', methods=['GET', 'POST'])
def register():
    if Setting().get('signup_enabled'):
        if request.method == 'GET':
            return render_template('register.html')
        elif request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            firstname = request.form.get('firstname')
            lastname = request.form.get('lastname')
            email = request.form.get('email')
            rpassword = request.form.get('rpassword')

            if not username or not password or not email:
                return render_template(
                    'register.html', error='Please input required information')

            if password != rpassword:
                return render_template(
                    'register.html',
                    error="Password confirmation does not match")

            user = User(username=username,
                        plain_text_password=password,
                        firstname=firstname,
                        lastname=lastname,
                        email=email)

            try:
                result = user.create_local_user()
                if result and result['status']:
                    if Setting().get('verify_user_email'):
                        send_account_verification(email)
                    return redirect(url_for('index.login'))
                else:
                    return render_template('register.html',
                                           error=result['msg'])
            except Exception as e:
                return render_template('register.html', error=e)
    else:
        return render_template('errors/404.html'), 404


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
def dyndns_checkip():
    # This route covers the default ddclient 'web' setting for the checkip service
    return render_template('dyndns.html',
                           response=request.environ.get(
                               'HTTP_X_REAL_IP', request.remote_addr))


@index_bp.route('/nic/update', methods=['GET', 'POST'])
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
                            request.remote_addr).split(', ')[:1])

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
                    created_by=current_user.username)
                history.add()
            else:
                oldip = r.data
                result = r.update(domain.name, str(ip))
                if result['status'] == 'ok':
                    history = History(
                        msg='DynDNS update: updated {} successfully'.format(hostname),
                        detail=str({
                            "domain": domain.name,
                            "record": hostname,
                            "type": rtype,
                            "old_value": oldip,
                            "new_value": str(ip)
                        }),
                        created_by=current_user.username)
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
                        detail=str({
                            "domain": domain.name,
                            "record": hostname,
                            "value": str(ip)
                        }),
                        created_by=current_user.username)
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
    if not current_app.config.get('SAML_ENABLED'):
        abort(400)
    req = saml.prepare_flask_request(request)
    auth = saml.init_saml_auth(req)
    redirect_url = OneLogin_Saml2_Utils.get_self_url(req) + url_for(
        'index.saml_authorized')
    return redirect(auth.login(return_to=redirect_url))


@index_bp.route('/saml/metadata')
def saml_metadata():
    if not current_app.config.get('SAML_ENABLED'):
        current_app.logger.error("SAML authentication is disabled.")
        abort(400)

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
def saml_authorized():
    errors = []
    if not current_app.config.get('SAML_ENABLED'):
        current_app.logger.error("SAML authentication is disabled.")
        abort(400)
    req = saml.prepare_flask_request(request)
    auth = saml.init_saml_auth(req)
    auth.process_response()
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
            user_accounts = set(user.get_account())
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
        login_user(user, remember=False)
        signin_history(user.username, 'SAML', True)
        return redirect(url_for('index.login'))
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


def handle_account(account_name):
    clean_name = ''.join(c for c in account_name.lower()
                         if c in "abcdefghijklmnopqrstuvwxyz0123456789")
    if len(clean_name) > Account.name.type.length:
        current_app.logger.error(
            "Account name {0} too long. Truncated.".format(clean_name))
    account = Account.query.filter_by(name=clean_name).first()
    if not account:
        account = Account(name=clean_name.lower(),
                          description='',
                          contact='',
                          mail='')
        account.create_account()
        history = History(msg='Account {0} created'.format(account.name),
                          created_by='SAML Assertion')
        history.add()
    return account


def uplift_to_admin(user):
    if user.role.name != 'Administrator':
        user.role_id = Role.query.filter_by(name='Administrator').first().id
        history = History(msg='Promoting {0} to administrator'.format(
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
