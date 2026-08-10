from flask import Blueprint, render_template, make_response, url_for, current_app, session, request, redirect, abort

from .auth_session import authenticate_user, clear_session
from .base import csrf
from ..models.user import User
from ..models.history import History
from ..services.identity_provisioning import (
    record_user_creation, handle_account, uplift_to_admin,
    uplift_to_operator, demote_to_user)
from ..services.saml import SAML

saml_bp = Blueprint('saml',
                    __name__,
                    template_folder='templates',
                    url_prefix='/')

_SAML_CLIENT_KEY = 'pda_saml_client'


def ensure_saml_client():
    """Lazily create the SAML helper once per app and store it on extensions."""
    client = current_app.extensions.get(_SAML_CLIENT_KEY)
    if client is not None:
        return client
    client = SAML()
    current_app.extensions[_SAML_CLIENT_KEY] = client
    return client


def start_idp_logout():
    """Begin SAML IdP-initiated single logout when a SAML session is active."""
    saml = ensure_saml_client()
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


def create_group_to_account_mapping():
    group_to_account_mapping_string = current_app.config.get(
        'SAML_GROUP_TO_ACCOUNT_MAPPING', None)
    if group_to_account_mapping_string and len(
            group_to_account_mapping_string.strip()) > 0:
        group_to_account_mapping = group_to_account_mapping_string.split(',')
    else:
        group_to_account_mapping = []
    return group_to_account_mapping


@saml_bp.route('/saml/login')
def saml_login():
    if not current_app.config.get('SAML_ENABLED', False):
        abort(400)
    from onelogin.saml2.utils import OneLogin_Saml2_Utils
    saml = ensure_saml_client()
    req = saml.prepare_flask_request(request)
    auth = saml.init_saml_auth(req)
    redirect_url = OneLogin_Saml2_Utils.get_self_url(req) + url_for(
        'saml.saml_authorized')
    return redirect(auth.login(return_to=redirect_url))


@saml_bp.route('/saml/metadata')
def saml_metadata():
    if not current_app.config.get('SAML_ENABLED', False):
        current_app.logger.error("SAML authentication is disabled.")
        abort(400)
    saml = ensure_saml_client()
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


@saml_bp.route('/saml/authorized', methods=['GET', 'POST'])
@csrf.exempt
def saml_authorized():
    errors = []
    if not current_app.config.get('SAML_ENABLED', False):
        current_app.logger.error("SAML authentication is disabled.")
        abort(400)
    from onelogin.saml2.utils import OneLogin_Saml2_Utils
    saml = ensure_saml_client()
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
        user_created = user is None
        if not user:
            user = User(username=username,
                        plain_text_password=None,
                        email=session['samlNameId'])
            result = user.create_local_user()
            if not result['status']:
                current_app.logger.error(
                    'SAML provisioning failed for user %s: %s', username,
                    result['msg'])
                clear_session()
                return render_template(
                    'errors/SAML.html',
                    errors=['Unable to provision the local user account.']), 400
            record_user_creation(user, audit_actor='SAML Assertion')
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
                    account = handle_account(
                        account_name, audit_actor='SAML Assertion')
                    saml_accounts.append(account)

            for account_name in session['samlUserdata'].get(
                    account_attribute_name, []):
                account = handle_account(
                    account_name, audit_actor='SAML Assertion')
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
            uplift_to_admin(user, audit_actor='SAML Assertion')
        elif admin_group_name in user_groups:
            uplift_to_admin(user, audit_actor='SAML Assertion')
        elif operator_group_name in user_groups:
            uplift_to_operator(user, audit_actor='SAML Assertion')
        elif admin_attribute_name or group_attribute_name:
            demote_to_user(user, audit_actor='SAML Assertion')
        user.plain_text_password = None
        if not user.update_profile():
            current_app.logger.error(
                'SAML provisioning failed while updating local user %s',
                username)
            clear_session()
            return render_template(
                'errors/SAML.html',
                errors=['Unable to update the local user account.']), 400

        accounts = sorted(account.name for account in user.get_accounts())
        current_app.logger.info(
            'SAML provisioning completed for user %s: local_user=%s, '
            'role=%s, accounts=%s', username,
            'created' if user_created else 'existing', user.role.name,
            accounts)
        session['authentication_type'] = 'SAML'
        return authenticate_user(user, 'SAML')
    else:
        return render_template('errors/SAML.html', errors=errors)


@saml_bp.route('/saml/sls')
def saml_logout():
    saml = ensure_saml_client()
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
            return redirect(url_for('index.login'))
    else:
        return render_template('errors/SAML.html', errors=errors)
