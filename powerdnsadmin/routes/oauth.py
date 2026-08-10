import json
import re
from collections.abc import Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from flask import Blueprint, render_template, url_for, current_app, session, request, redirect, abort
from flask_login import logout_user
from authlib.integrations.base_client.errors import MismatchingStateError

from .auth_session import authenticate_user
from ..models.base import db
from ..models.user import User
from ..models.account import Account
from ..models.setting import Setting
from ..models.history import History
from ..services.identity_provisioning import handle_account, record_user_creation
from ..services.google import google_oauth
from ..services.github import github_oauth
from ..services.azure import azure_oauth
from ..services.oidc import merge_oidc_claims, oidc_oauth

oauth_bp = Blueprint('oauth',
                     __name__,
                     template_folder='templates',
                     url_prefix='/')

_OAUTH_CLIENTS_KEY = 'pda_oauth_clients'


def ensure_oauth_clients():
    """Lazily create Authlib clients once per app and store them on extensions."""
    clients = current_app.extensions.get(_OAUTH_CLIENTS_KEY)
    if clients is not None:
        return clients
    clients = {
        'google': google_oauth(),
        'github': github_oauth(),
        'azure': azure_oauth(),
        'oidc': oidc_oauth(),
    }
    current_app.extensions[_OAUTH_CLIENTS_KEY] = clients
    return clients


def get_oauth_client(provider):
    return ensure_oauth_clients().get(provider)


def handle_stale_oauth_callback():
    """Recover from a stale OAuth state after an IdP redirect.

    Mirrors expired login/registration CSRF handling: clear any partial
    session and return a fresh login page instead of a 500.
    """
    logout_user()
    session.clear()
    session['_remember'] = 'clear'
    return render_template(
        'login.html',
        saml_enabled=current_app.config.get('SAML_ENABLED', False),
        error='Your sign-in session expired. Please try again.',
    ), 400


def authorize_oauth_access_token(client):
    try:
        return client.authorize_access_token(), None
    except MismatchingStateError:
        current_app.logger.info(
            'OAuth callback state mismatch; clearing session for a fresh login')
        return None, handle_stale_oauth_callback()


def external_url_params():
    """Build the url_for() kwargs used for externally-facing OAuth redirect URIs."""
    use_ssl = current_app.config.get('SERVER_EXTERNAL_SSL')
    params = {'_external': True}
    if isinstance(use_ssl, bool):
        params['_scheme'] = 'https' if use_ssl else 'http'
    return params


def oidc_logout_url():
    """Build an OpenID Connect RP-Initiated Logout 1.0 request URL.

    Prefer the provider's discovered ``end_session_endpoint`` and retain the
    configured logout URL as a fallback for providers without discovery
    metadata. Returning ``None`` deliberately falls back to local logout.
    """
    token = session.get('oidc_token')
    if not isinstance(token, Mapping):
        return None

    configured_endpoint = Setting().get('oidc_oauth_logout_url')
    endpoint = None
    oidc = get_oauth_client('oidc')
    if oidc is not None:
        try:
            metadata = oidc.load_server_metadata()
            if isinstance(metadata, Mapping):
                endpoint = metadata.get('end_session_endpoint')
        except Exception as e:
            current_app.logger.warning(
                'OIDC: unable to discover the logout endpoint (%s); '
                'using the configured logout URL if available', e)

    if not isinstance(endpoint, str) or not endpoint.strip():
        endpoint = None
    if not endpoint and isinstance(configured_endpoint, str):
        endpoint = configured_endpoint.strip()
    if not endpoint:
        current_app.logger.info(
            'OIDC provider does not publish or configure a logout endpoint; '
            'performing local logout only')
        return None

    post_logout_redirect_uri = url_for(
        'index.login', **external_url_params())
    parameters = {
        'post_logout_redirect_uri': post_logout_redirect_uri,
    }
    id_token = token.get('id_token')
    if id_token:
        parameters['id_token_hint'] = id_token

    client_id = Setting().get('oidc_oauth_key')
    if client_id:
        parameters['client_id'] = client_id

    endpoint_parts = urlsplit(endpoint)
    query = dict(parse_qsl(endpoint_parts.query, keep_blank_values=True))
    query.update(parameters)
    return urlunsplit(endpoint_parts._replace(query=urlencode(query)))


def oauth_login(client, setting_key, provider_key, provider_label):
    """Shared handler for the '/<provider>/login' routes: kick off the
    Authlib redirect to the provider, once its client is enabled and ready.
    """
    if not Setting().get(setting_key) or client is None:
        current_app.logger.error(
            '%s OAuth is disabled or you have not yet reloaded the pda application after enabling.'
            % provider_label
        )
        abort(400)
    redirect_uri = url_for(f'oauth.{provider_key}_authorized', **external_url_params())
    return client.authorize_redirect(redirect_uri)


def oauth_authorized(client, setting_key, provider_key, provider_label,
                     token_session_key, reason_param='error'):
    """Shared handler for the '/<provider>/authorized' callbacks: exchange
    the Authlib code for a token, then resolve it into an authenticated User.
    """
    if not Setting().get(setting_key) or client is None:
        current_app.logger.error(
            '%s OAuth is disabled or you have not yet reloaded the pda application after enabling.'
            % provider_label
        )
        abort(400)
    params = external_url_params()
    authorized_endpoint = f'oauth.{provider_key}_authorized'
    session[f'{provider_key}_oauthredir'] = url_for(authorized_endpoint, **params)
    token, stale_response = authorize_oauth_access_token(client)
    if stale_response is not None:
        return stale_response
    if token is None:
        msg = 'Access denied: reason=%s error=%s' % (
            request.args.get(reason_param, 'unknown'),
            request.args.get('error_description', 'unknown'),
        )
        return render_template('errors/400.html', msg=msg), 400
    session[token_session_key] = token
    return complete_provider_login(provider_key)


def complete_provider_login(provider_key):
    completers = {
        'google': complete_google_login,
        'github': complete_github_login,
        'azure': complete_azure_login,
        'oidc': complete_oidc_login,
    }
    completer = completers.get(provider_key)
    if completer is None:
        abort(400)
    return completer()


def log_oauth_provisioning(provider_label, user, user_created):
    accounts = sorted(account.name for account in user.get_accounts())
    current_app.logger.info(
        '%s provisioning completed for user %s: local_user=%s, role=%s, '
        'accounts=%s', provider_label, user.username,
        'created' if user_created else 'existing', user.role.name, accounts)


def get_azure_groups(uri):
    azure = get_oauth_client('azure')
    azure_info = azure.get(uri).text
    current_app.logger.info('Microsoft Entra ID groups returned: ' + azure_info)
    grouplookup = json.loads(azure_info)
    if "value" in grouplookup:
        mygroups = grouplookup["value"]
        if "@odata.nextLink" in grouplookup:
            mygroups.extend(get_azure_groups(grouplookup["@odata.nextLink"]))
    else:
        mygroups = []
    return mygroups


def complete_google_login():
    google = get_oauth_client('google')
    user_data = json.loads(google.get('userinfo').text)
    google_first_name = user_data['given_name']
    google_last_name = user_data['family_name']
    google_email = user_data['email']
    user = User.query.filter_by(username=google_email).first()
    if user is None:
        user = User.query.filter_by(email=google_email).first()
    user_created = user is None
    if not user:
        user = User(username=google_email,
                    firstname=google_first_name,
                    lastname=google_last_name,
                    plain_text_password=None,
                    email=google_email)

        result = user.create_local_user()
        if not result['status']:
            current_app.logger.error(
                'Google OAuth provisioning failed for user %s: %s',
                google_email, result['msg'])
            session.pop('google_token', None)
            return redirect(url_for('index.login'))
        record_user_creation(user, audit_actor='Google OAuth')

    session['user_id'] = user.id
    session['authentication_type'] = 'OAuth'
    log_oauth_provisioning('Google OAuth', user, user_created)
    return authenticate_user(user, 'Google OAuth')


def complete_github_login():
    github = get_oauth_client('github')
    user_data = json.loads(github.get('user').text)
    github_username = user_data['login']
    github_first_name = user_data['name']
    github_last_name = ''
    github_email = user_data['email']

    github_name_parts = github_first_name.split(' ')
    if len(github_name_parts) > 1:
        github_first_name = github_name_parts[0]
        github_last_name = ' '.join(github_name_parts[1:])

    user = User.query.filter_by(username=github_username).first()
    if user is None:
        user = User.query.filter_by(email=github_email).first()
    user_created = user is None
    if not user:
        user = User(username=github_username,
                    plain_text_password=None,
                    firstname=github_first_name,
                    lastname=github_last_name,
                    email=github_email)

        result = user.create_local_user()
        if not result['status']:
            current_app.logger.error(
                'GitHub OAuth provisioning failed for user %s: %s',
                github_username, result['msg'])
            session.pop('github_token', None)
            return redirect(url_for('index.login'))
        record_user_creation(user, audit_actor='GitHub OAuth')

    session['user_id'] = user.id
    session['authentication_type'] = 'OAuth'
    log_oauth_provisioning('GitHub OAuth', user, user_created)
    return authenticate_user(user, 'GitHub OAuth')


def complete_azure_login():
    azure = get_oauth_client('azure')
    saml_enabled = current_app.config.get('SAML_ENABLED', False)
    azure_info = azure.get(
        'me?$select=displayName,givenName,id,mail,surname,userPrincipalName').text
    current_app.logger.info('Microsoft Entra ID login returned: ' + azure_info)
    user_data = json.loads(azure_info)

    azure_info = azure.post('me/getMemberGroups',
                            json={'securityEnabledOnly': False}).text
    current_app.logger.info('Microsoft Entra ID groups returned: ' + azure_info)
    grouplookup = json.loads(azure_info)
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

    azure_email = re.sub(r"#.*$", "", azure_email)
    azure_username = re.sub(r"#.*$", "", azure_username)

    user = User.query.filter_by(username=azure_username).first()
    user_created = user is None
    if not user:
        user = User(username=azure_username,
                    plain_text_password=None,
                    firstname=azure_first_name,
                    lastname=azure_last_name,
                    email=azure_email)

        result = user.create_local_user()
        if not result['status']:
            current_app.logger.error(
                'Microsoft Entra ID OAuth provisioning failed for user %s: %s',
                azure_username, result['msg'])
            session.pop('azure_token', None)
            return render_template('login.html',
                                   saml_enabled=saml_enabled,
                                   error=('User ' + azure_username +
                                          ' cannot be created.'))
        record_user_creation(
            user, audit_actor='Microsoft Entra ID OAuth')

    session['user_id'] = user.id
    session['authentication_type'] = 'OAuth'

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
                                           saml_enabled=saml_enabled,
                                           error=('User ' + azure_username +
                                                  ' is not in any authorised groups.'))

    if Setting().get('azure_group_accounts_enabled') and mygroups:
        current_app.logger.info(
            'Microsoft Entra ID group account sync enabled')
        name_value = Setting().get('azure_group_accounts_name')
        description_value = Setting().get('azure_group_accounts_description')
        select_values = name_value
        if description_value != '':
            select_values += ',' + description_value

        mygroups = get_azure_groups(
            'me/memberOf/microsoft.graph.group?$count=false&$securityEnabled=true&$select={}'.format(select_values))

        description_pattern = Setting().get('azure_group_accounts_description_re')
        pattern = Setting().get('azure_group_accounts_name_re')

        for azure_group in mygroups:
            if name_value in azure_group:
                group_name = azure_group[name_value]
                group_description = ''
                if description_value in azure_group:
                    group_description = azure_group[description_value]

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
                            continue

                if pattern != '':
                    current_app.logger.info(
                        'Matching group name {} against regex {}'.format(group_name, pattern))
                    matches = re.match(pattern, group_name)
                    if matches:
                        current_app.logger.info(
                            'Group {} matched regexp'.format(group_name))
                        group_name = matches.group(1)
                    else:
                        continue

                account = Account()
                sanitized_group_name = Account.sanitize_name(group_name)
                account_id = account.get_id_by_name(account_name=sanitized_group_name)

                if account_id:
                    account = db.session.get(Account, account_id)
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

    log_oauth_provisioning(
        'Microsoft Entra ID OAuth', user, user_created)
    return authenticate_user(user, 'Microsoft Entra ID OAuth')


def complete_oidc_login():
    oidc = get_oauth_client('oidc')
    try:
        oidc_metadata = oidc.load_server_metadata()
    except Exception as e:
        current_app.logger.warning(
            'OIDC: unable to load server metadata ({}); '
            'falling back to relative userinfo endpoint'.format(e))
        oidc_metadata = {}

    userinfo_endpoint = oidc_metadata.get('userinfo_endpoint')
    try:
        if userinfo_endpoint:
            userinfo_resp = oidc.get(userinfo_endpoint, timeout=15)
        else:
            userinfo_resp = oidc.get('userinfo', timeout=15)
        userinfo_resp.raise_for_status()
        user_data = merge_oidc_claims(
            session.get('oidc_token'), userinfo_resp.json())
    except Exception as e:
        current_app.logger.error('OIDC: failed to fetch userinfo: {}'.format(e))
        session.pop('oidc_token', None)
        return redirect(url_for('index.login'))

    oidc_username = user_data.get(Setting().get('oidc_oauth_username'))
    oidc_first_name = user_data.get(Setting().get('oidc_oauth_firstname'), '')
    oidc_last_name = user_data.get(Setting().get('oidc_oauth_last_name'), '')
    oidc_email = user_data.get(Setting().get('oidc_oauth_email'), '')

    if not oidc_username:
        current_app.logger.error(
            'OIDC: username claim "{}" not present in OIDC claims'.format(
                Setting().get('oidc_oauth_username')))
        session.pop('oidc_token', None)
        return redirect(url_for('index.login'))

    user = User.query.filter_by(username=oidc_username).first()
    user_created = user is None
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
        current_app.logger.error(
            'OIDC provisioning failed for user %s: %s', oidc_username,
            result['msg'])
        session.pop('oidc_token', None)
        return redirect(url_for('index.login'))
    if user_created:
        record_user_creation(user, audit_actor='OIDC Assertion')

    if Setting().get('oidc_oauth_account_name_property') and Setting().get(
            'oidc_oauth_account_description_property'):

        name_prop = Setting().get('oidc_oauth_account_name_property')
        desc_prop = Setting().get('oidc_oauth_account_description_property')

        account_to_add = []
        if name_prop in user_data and desc_prop in user_data:
            accounts_name_prop = [user_data[name_prop]] if type(user_data[name_prop]) is not list else user_data[name_prop]
            accounts_desc_prop = [user_data[desc_prop]] if type(user_data[desc_prop]) is not list else user_data[desc_prop]

            for i in range(len(accounts_name_prop)):
                description = ''
                if i < len(accounts_desc_prop):
                    description = accounts_desc_prop[i]
                account = handle_account(
                    accounts_name_prop[i],
                    description,
                    audit_actor='OIDC Assertion')

                account_to_add.append(account)
            user_accounts = user.get_accounts()

            for account in account_to_add:
                if account not in user_accounts:
                    account.add_user(user)

            if Setting().get('delete_sso_accounts'):
                for account in user_accounts:
                    if account not in account_to_add:
                        account.remove_user(user)

    session['user_id'] = user.id
    session['authentication_type'] = 'OAuth'
    log_oauth_provisioning('OIDC', user, user_created)
    return authenticate_user(user, 'OIDC OAuth')


@oauth_bp.route('/google/login')
def google_login():
    return oauth_login(get_oauth_client('google'), 'google_oauth_enabled', 'google', 'Google')


@oauth_bp.route('/google/authorized')
def google_authorized():
    return oauth_authorized(get_oauth_client('google'), 'google_oauth_enabled', 'google', 'Google',
                            'google_token', reason_param='error_reason')


@oauth_bp.route('/github/login')
def github_login():
    return oauth_login(get_oauth_client('github'), 'github_oauth_enabled', 'github', 'Github')


@oauth_bp.route('/github/authorized')
def github_authorized():
    return oauth_authorized(get_oauth_client('github'), 'github_oauth_enabled', 'github', 'Github', 'github_token')


@oauth_bp.route('/azure/login')
def azure_login():
    return oauth_login(get_oauth_client('azure'), 'azure_oauth_enabled',
                       'azure', 'Microsoft Entra ID')


@oauth_bp.route('/azure/authorized')
def azure_authorized():
    return oauth_authorized(get_oauth_client('azure'), 'azure_oauth_enabled',
                            'azure', 'Microsoft Entra ID', 'azure_token')


@oauth_bp.route('/oidc/login')
def oidc_login():
    return oauth_login(get_oauth_client('oidc'), 'oidc_oauth_enabled', 'oidc', 'OIDC')


@oauth_bp.route('/oidc/authorized')
def oidc_authorized():
    return oauth_authorized(get_oauth_client('oidc'), 'oidc_oauth_enabled', 'oidc', 'OIDC', 'oidc_token')
