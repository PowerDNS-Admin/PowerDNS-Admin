import json
import datetime
import traceback
from ast import literal_eval
from flask import Blueprint, render_template, make_response, url_for, current_app, request, redirect, jsonify, abort, flash, session
from flask_login import login_required, current_user

from ..decorators import operator_role_required, admin_role_required
from ..models.user import User
from ..models.account import Account
from ..models.account_user import AccountUser
from ..models.role import Role
from ..models.server import Server
from ..models.setting import Setting
from ..models.history import History
from ..models.domain import Domain
from ..models.record import Record
from ..models.domain_template import DomainTemplate
from ..models.domain_template_record import DomainTemplateRecord

admin_bp = Blueprint('admin',
                     __name__,
                     template_folder='templates',
                     url_prefix='/admin')


@admin_bp.before_request
def before_request():
    # Manage session timeout
    session.permanent = True
    current_app.permanent_session_lifetime = datetime.timedelta(
        minutes=int(Setting().get('session_timeout')))
    session.modified = True



@admin_bp.route('/pdns', methods=['GET'])
@login_required
@operator_role_required
def pdns_stats():
    if not Setting().get('pdns_api_url') or not Setting().get(
            'pdns_api_key') or not Setting().get('pdns_version'):
        return redirect(url_for('admin.setting_pdns'))

    domains = Domain.query.all()
    users = User.query.all()

    server = Server(server_id='localhost')
    configs = server.get_config()
    statistics = server.get_statistic()
    history_number = History.query.count()

    if statistics:
        uptime = list([
            uptime for uptime in statistics if uptime['name'] == 'uptime'
        ])[0]['value']
    else:
        uptime = 0

    return render_template('admin_pdns_stats.html',
                           domains=domains,
                           users=users,
                           configs=configs,
                           statistics=statistics,
                           uptime=uptime,
                           history_number=history_number)


@admin_bp.route('/user/edit/<user_username>', methods=['GET', 'POST'])
@admin_bp.route('/user/edit', methods=['GET', 'POST'])
@login_required
@operator_role_required
def edit_user(user_username=None):
    if user_username:
        user = User.query.filter(User.username == user_username).first()
        create = False

        if not user:
            return render_template('errors/404.html'), 404

        if user.role.name == 'Administrator' and current_user.role.name != 'Administrator':
            return render_template('errors/401.html'), 401
    else:
        user = None
        create = True

    if request.method == 'GET':
        return render_template('admin_edit_user.html',
                               user=user,
                               create=create)

    elif request.method == 'POST':
        fdata = request.form

        if create:
            user_username = fdata['username']

        user = User(username=user_username,
                    plain_text_password=fdata['password'],
                    firstname=fdata['firstname'],
                    lastname=fdata['lastname'],
                    email=fdata['email'],
                    reload_info=False)

        if create:
            if fdata['password'] == "":
                return render_template('admin_edit_user.html',
                                       user=user,
                                       create=create,
                                       blank_password=True)

            result = user.create_local_user()
            history = History(msg='Created user {0}'.format(user.username),
                              created_by=current_user.username)

        else:
            result = user.update_local_user()
            history = History(msg='Updated user {0}'.format(user.username),
                              created_by=current_user.username)

        if result['status']:
            history.add()
            return redirect(url_for('admin.manage_user'))

        return render_template('admin_edit_user.html',
                               user=user,
                               create=create,
                               error=result['msg'])


@admin_bp.route('/manage-user', methods=['GET', 'POST'])
@login_required
@operator_role_required
def manage_user():
    if request.method == 'GET':
        roles = Role.query.all()
        users = User.query.order_by(User.username).all()
        return render_template('admin_manage_user.html',
                               users=users,
                               roles=roles)

    if request.method == 'POST':
        #
        # post data should in format
        # {'action': 'delete_user', 'data': 'username'}
        #
        try:
            jdata = request.json
            data = jdata['data']

            if jdata['action'] == 'user_otp_disable':
                user = User(username=data)
                result = user.update_profile(enable_otp=False)
                if result:
                    history = History(
                        msg='Two factor authentication disabled for user {0}'.
                        format(data),
                        created_by=current_user.username)
                    history.add()
                    return make_response(
                        jsonify({
                            'status':
                            'ok',
                            'msg':
                            'Two factor authentication has been disabled for user.'
                        }), 200)
                else:
                    return make_response(
                        jsonify({
                            'status':
                            'error',
                            'msg':
                            'Cannot disable two factor authentication for user.'
                        }), 500)

            elif jdata['action'] == 'delete_user':
                user = User(username=data)
                if user.username == current_user.username:
                    return make_response(
                        jsonify({
                            'status': 'error',
                            'msg': 'You cannot delete yourself.'
                        }), 400)

                # Remove account associations first
                user_accounts = Account.query.join(AccountUser).join(
                    User).filter(AccountUser.user_id == user.id,
                                 AccountUser.account_id == Account.id).all()
                for uc in user_accounts:
                    uc.revoke_privileges_by_id(user.id)

                # Then delete the user
                result = user.delete()
                if result:
                    history = History(msg='Delete user {0}'.format(data),
                                      created_by=current_user.username)
                    history.add()
                    return make_response(
                        jsonify({
                            'status': 'ok',
                            'msg': 'User has been removed.'
                        }), 200)
                else:
                    return make_response(
                        jsonify({
                            'status': 'error',
                            'msg': 'Cannot remove user.'
                        }), 500)

            elif jdata['action'] == 'revoke_user_privileges':
                user = User(username=data)
                result = user.revoke_privilege()
                if result:
                    history = History(
                        msg='Revoke {0} user privileges'.format(data),
                        created_by=current_user.username)
                    history.add()
                    return make_response(
                        jsonify({
                            'status': 'ok',
                            'msg': 'Revoked user privileges.'
                        }), 200)
                else:
                    return make_response(
                        jsonify({
                            'status': 'error',
                            'msg': 'Cannot revoke user privilege.'
                        }), 500)

            elif jdata['action'] == 'update_user_role':
                username = data['username']
                role_name = data['role_name']

                if username == current_user.username:
                    return make_response(
                        jsonify({
                            'status': 'error',
                            'msg': 'You cannot change you own roles.'
                        }), 400)

                user = User.query.filter(User.username == username).first()
                if not user:
                    return make_response(
                        jsonify({
                            'status': 'error',
                            'msg': 'User does not exist.'
                        }), 404)

                if user.role.name == 'Administrator' and current_user.role.name != 'Administrator':
                    return make_response(
                        jsonify({
                            'status':
                            'error',
                            'msg':
                            'You do not have permission to change Administrator users role.'
                        }), 400)

                if role_name == 'Administrator' and current_user.role.name != 'Administrator':
                    return make_response(
                        jsonify({
                            'status':
                            'error',
                            'msg':
                            'You do not have permission to promote a user to Administrator role.'
                        }), 400)

                user = User(username=username)
                result = user.set_role(role_name)
                if result['status']:
                    history = History(
                        msg='Change user role of {0} to {1}'.format(
                            username, role_name),
                        created_by=current_user.username)
                    history.add()
                    return make_response(
                        jsonify({
                            'status': 'ok',
                            'msg': 'Changed user role successfully.'
                        }), 200)
                else:
                    return make_response(
                        jsonify({
                            'status':
                            'error',
                            'msg':
                            'Cannot change user role. {0}'.format(
                                result['msg'])
                        }), 500)
            else:
                return make_response(
                    jsonify({
                        'status': 'error',
                        'msg': 'Action not supported.'
                    }), 400)
        except Exception as e:
            current_app.logger.error(
                'Cannot update user. Error: {0}'.format(e))
            current_app.logger.debug(traceback.format_exc())
            return make_response(
                jsonify({
                    'status':
                    'error',
                    'msg':
                    'There is something wrong, please contact Administrator.'
                }), 400)


@admin_bp.route('/account/edit/<account_name>', methods=['GET', 'POST'])
@admin_bp.route('/account/edit', methods=['GET', 'POST'])
@login_required
@operator_role_required
def edit_account(account_name=None):
    users = User.query.all()

    if request.method == 'GET':
        if account_name is None:
            return render_template('admin_edit_account.html',
                                   users=users,
                                   create=1)

        else:
            account = Account.query.filter(
                Account.name == account_name).first()
            account_user_ids = account.get_user()
            return render_template('admin_edit_account.html',
                                   account=account,
                                   account_user_ids=account_user_ids,
                                   users=users,
                                   create=0)

    if request.method == 'POST':
        fdata = request.form
        new_user_list = request.form.getlist('account_multi_user')

        # on POST, synthesize account and account_user_ids from form data
        if not account_name:
            account_name = fdata['accountname']

        account = Account(name=account_name,
                          description=fdata['accountdescription'],
                          contact=fdata['accountcontact'],
                          mail=fdata['accountmail'])
        account_user_ids = []
        for username in new_user_list:
            userid = User(username=username).get_user_info_by_username().id
            account_user_ids.append(userid)

        create = int(fdata['create'])
        if create:
            # account __init__ sanitizes and lowercases the name, so to manage expectations
            # we let the user reenter the name until it's not empty and it's valid (ignoring the case)
            if account.name == "" or account.name != account_name.lower():
                return render_template('admin_edit_account.html',
                                       account=account,
                                       account_user_ids=account_user_ids,
                                       users=users,
                                       create=create,
                                       invalid_accountname=True)

            if Account.query.filter(Account.name == account.name).first():
                return render_template('admin_edit_account.html',
                                       account=account,
                                       account_user_ids=account_user_ids,
                                       users=users,
                                       create=create,
                                       duplicate_accountname=True)

            result = account.create_account()
            history = History(msg='Create account {0}'.format(account.name),
                              created_by=current_user.username)

        else:
            result = account.update_account()
            history = History(msg='Update account {0}'.format(account.name),
                              created_by=current_user.username)

        if result['status']:
            account.grant_privileges(new_user_list)
            history.add()
            return redirect(url_for('admin.manage_account'))

        return render_template('admin_edit_account.html',
                               account=account,
                               account_user_ids=account_user_ids,
                               users=users,
                               create=create,
                               error=result['msg'])


@admin_bp.route('/manage-account', methods=['GET', 'POST'])
@login_required
@operator_role_required
def manage_account():
    if request.method == 'GET':
        accounts = Account.query.order_by(Account.name).all()
        for account in accounts:
            account.user_num = AccountUser.query.filter(
                AccountUser.account_id == account.id).count()
        return render_template('admin_manage_account.html', accounts=accounts)

    if request.method == 'POST':
        #
        # post data should in format
        # {'action': 'delete_account', 'data': 'accountname'}
        #
        try:
            jdata = request.json
            data = jdata['data']

            if jdata['action'] == 'delete_account':
                account = Account.query.filter(Account.name == data).first()
                if not account:
                    return make_response(
                        jsonify({
                            'status': 'error',
                            'msg': 'Account not found.'
                        }), 404)
                # Remove account association from domains first
                for domain in account.domains:
                    Domain(name=domain.name).assoc_account(None)
                # Then delete the account
                result = account.delete_account()
                if result:
                    history = History(msg='Delete account {0}'.format(data),
                                      created_by=current_user.username)
                    history.add()
                    return make_response(
                        jsonify({
                            'status': 'ok',
                            'msg': 'Account has been removed.'
                        }), 200)
                else:
                    return make_response(
                        jsonify({
                            'status': 'error',
                            'msg': 'Cannot remove account.'
                        }), 500)
            else:
                return make_response(
                    jsonify({
                        'status': 'error',
                        'msg': 'Action not supported.'
                    }), 400)
        except Exception as e:
            current_app.logger.error(
                'Cannot update account. Error: {0}'.format(e))
            current_app.logger.debug(traceback.format_exc())
            return make_response(
                jsonify({
                    'status':
                    'error',
                    'msg':
                    'There is something wrong, please contact Administrator.'
                }), 400)


@admin_bp.route('/history', methods=['GET', 'POST'])
@login_required
@operator_role_required
def history():
    if request.method == 'POST':
        if current_user.role.name != 'Administrator':
            return make_response(
                jsonify({
                    'status': 'error',
                    'msg': 'You do not have permission to remove history.'
                }), 401)

        h = History()
        result = h.remove_all()
        if result:
            history = History(msg='Remove all histories',
                              created_by=current_user.username)
            history.add()
            return make_response(
                jsonify({
                    'status': 'ok',
                    'msg': 'Changed user role successfully.'
                }), 200)
        else:
            return make_response(
                jsonify({
                    'status': 'error',
                    'msg': 'Can not remove histories.'
                }), 500)

    if request.method == 'GET':
        histories = History.query.all()
        return render_template('admin_history.html', histories=histories)


@admin_bp.route('/setting/basic', methods=['GET'])
@login_required
@operator_role_required
def setting_basic():
    if request.method == 'GET':
        settings = [
            'maintenance', 'fullscreen_layout', 'record_helper',
            'login_ldap_first', 'default_record_table_size',
            'default_domain_table_size', 'auto_ptr', 'record_quick_edit',
            'pretty_ipv6_ptr', 'dnssec_admins_only',
            'allow_user_create_domain', 'bg_domain_updates', 'site_name',
            'session_timeout', 'warn_session_timeout', 'ttl_options',
            'pdns_api_timeout', 'verify_ssl_connections', 'verify_user_email'
        ]

        return render_template('admin_setting_basic.html', settings=settings)


@admin_bp.route('/setting/basic/<path:setting>/edit', methods=['POST'])
@login_required
@operator_role_required
def setting_basic_edit(setting):
    jdata = request.json
    new_value = jdata['value']
    result = Setting().set(setting, new_value)

    if (result):
        return make_response(
            jsonify({
                'status': 'ok',
                'msg': 'Toggled setting successfully.'
            }), 200)
    else:
        return make_response(
            jsonify({
                'status': 'error',
                'msg': 'Unable to toggle setting.'
            }), 500)


@admin_bp.route('/setting/basic/<path:setting>/toggle', methods=['POST'])
@login_required
@operator_role_required
def setting_basic_toggle(setting):
    result = Setting().toggle(setting)
    if (result):
        return make_response(
            jsonify({
                'status': 'ok',
                'msg': 'Toggled setting successfully.'
            }), 200)
    else:
        return make_response(
            jsonify({
                'status': 'error',
                'msg': 'Unable to toggle setting.'
            }), 500)


@admin_bp.route('/setting/pdns', methods=['GET', 'POST'])
@login_required
@admin_role_required
def setting_pdns():
    if request.method == 'GET':
        pdns_api_url = Setting().get('pdns_api_url')
        pdns_api_key = Setting().get('pdns_api_key')
        pdns_version = Setting().get('pdns_version')
        return render_template('admin_setting_pdns.html',
                               pdns_api_url=pdns_api_url,
                               pdns_api_key=pdns_api_key,
                               pdns_version=pdns_version)
    elif request.method == 'POST':
        pdns_api_url = request.form.get('pdns_api_url')
        pdns_api_key = request.form.get('pdns_api_key')
        pdns_version = request.form.get('pdns_version')

        Setting().set('pdns_api_url', pdns_api_url)
        Setting().set('pdns_api_key', pdns_api_key)
        Setting().set('pdns_version', pdns_version)

        return render_template('admin_setting_pdns.html',
                               pdns_api_url=pdns_api_url,
                               pdns_api_key=pdns_api_key,
                               pdns_version=pdns_version)


@admin_bp.route('/setting/dns-records', methods=['GET', 'POST'])
@login_required
@operator_role_required
def setting_records():
    if request.method == 'GET':
        _fr = Setting().get('forward_records_allow_edit')
        _rr = Setting().get('reverse_records_allow_edit')
        f_records = literal_eval(_fr) if isinstance(_fr, str) else _fr
        r_records = literal_eval(_rr) if isinstance(_rr, str) else _rr

        return render_template('admin_setting_records.html',
                               f_records=f_records,
                               r_records=r_records)
    elif request.method == 'POST':
        fr = {}
        rr = {}
        records = Setting().defaults['forward_records_allow_edit']
        for r in records:
            fr[r] = True if request.form.get('fr_{0}'.format(
                r.lower())) else False
            rr[r] = True if request.form.get('rr_{0}'.format(
                r.lower())) else False

        Setting().set('forward_records_allow_edit', str(fr))
        Setting().set('reverse_records_allow_edit', str(rr))
        return redirect(url_for('admin.setting_records'))


@admin_bp.route('/setting/authentication', methods=['GET', 'POST'])
@login_required
@admin_role_required
def setting_authentication():
    if request.method == 'GET':
        return render_template('admin_setting_authentication.html')
    elif request.method == 'POST':
        conf_type = request.form.get('config_tab')
        result = None

        if conf_type == 'general':
            local_db_enabled = True if request.form.get(
                'local_db_enabled') else False
            signup_enabled = True if request.form.get(
                'signup_enabled', ) else False

            if not local_db_enabled and not Setting().get('ldap_enabled'):
                result = {
                    'status':
                    False,
                    'msg':
                    'Local DB and LDAP Authentication can not be disabled at the same time.'
                }
            else:
                Setting().set('local_db_enabled', local_db_enabled)
                Setting().set('signup_enabled', signup_enabled)
                result = {'status': True, 'msg': 'Saved successfully'}
        elif conf_type == 'ldap':
            ldap_enabled = True if request.form.get('ldap_enabled') else False

            if not ldap_enabled and not Setting().get('local_db_enabled'):
                result = {
                    'status':
                    False,
                    'msg':
                    'Local DB and LDAP Authentication can not be disabled at the same time.'
                }
            else:
                Setting().set('ldap_enabled', ldap_enabled)
                Setting().set('ldap_type', request.form.get('ldap_type'))
                Setting().set('ldap_uri', request.form.get('ldap_uri'))
                Setting().set('ldap_base_dn', request.form.get('ldap_base_dn'))
                Setting().set('ldap_admin_username',
                              request.form.get('ldap_admin_username'))
                Setting().set('ldap_admin_password',
                              request.form.get('ldap_admin_password'))
                Setting().set('ldap_filter_basic',
                              request.form.get('ldap_filter_basic'))
                Setting().set('ldap_filter_group',
                              request.form.get('ldap_filter_group'))
                Setting().set('ldap_filter_username',
                              request.form.get('ldap_filter_username'))
                Setting().set('ldap_filter_groupname',
                              request.form.get('ldap_filter_groupname'))
                Setting().set(
                    'ldap_sg_enabled', True
                    if request.form.get('ldap_sg_enabled') == 'ON' else False)
                Setting().set('ldap_admin_group',
                              request.form.get('ldap_admin_group'))
                Setting().set('ldap_operator_group',
                              request.form.get('ldap_operator_group'))
                Setting().set('ldap_user_group',
                              request.form.get('ldap_user_group'))
                Setting().set('ldap_domain', request.form.get('ldap_domain'))
                result = {'status': True, 'msg': 'Saved successfully'}
        elif conf_type == 'google':
            Setting().set(
                'google_oauth_enabled',
                True if request.form.get('google_oauth_enabled') else False)
            Setting().set('google_oauth_client_id',
                          request.form.get('google_oauth_client_id'))
            Setting().set('google_oauth_client_secret',
                          request.form.get('google_oauth_client_secret'))
            Setting().set('google_token_url',
                          request.form.get('google_token_url'))
            Setting().set('google_oauth_scope',
                          request.form.get('google_oauth_scope'))
            Setting().set('google_authorize_url',
                          request.form.get('google_authorize_url'))
            Setting().set('google_base_url',
                          request.form.get('google_base_url'))
            result = {
                'status': True,
                'msg': 'Saved successfully. Please reload PDA to take effect.'
            }
        elif conf_type == 'github':
            Setting().set(
                'github_oauth_enabled',
                True if request.form.get('github_oauth_enabled') else False)
            Setting().set('github_oauth_key',
                          request.form.get('github_oauth_key'))
            Setting().set('github_oauth_secret',
                          request.form.get('github_oauth_secret'))
            Setting().set('github_oauth_scope',
                          request.form.get('github_oauth_scope'))
            Setting().set('github_oauth_api_url',
                          request.form.get('github_oauth_api_url'))
            Setting().set('github_oauth_token_url',
                          request.form.get('github_oauth_token_url'))
            Setting().set('github_oauth_authorize_url',
                          request.form.get('github_oauth_authorize_url'))
            result = {
                'status': True,
                'msg': 'Saved successfully. Please reload PDA to take effect.'
            }
        elif conf_type == 'azure':
            Setting().set(
                'azure_oauth_enabled',
                True if request.form.get('azure_oauth_enabled') else False)
            Setting().set('azure_oauth_key',
                          request.form.get('azure_oauth_key'))
            Setting().set('azure_oauth_secret',
                          request.form.get('azure_oauth_secret'))
            Setting().set('azure_oauth_scope',
                          request.form.get('azure_oauth_scope'))
            Setting().set('azure_oauth_api_url',
                          request.form.get('azure_oauth_api_url'))
            Setting().set('azure_oauth_token_url',
                          request.form.get('azure_oauth_token_url'))
            Setting().set('azure_oauth_authorize_url',
                          request.form.get('azure_oauth_authorize_url'))
            Setting().set('azure_sg_enabled', True if request.form.get('azure_sg_enabled')=='ON' else False)
            Setting().set('azure_admin_group', request.form.get('azure_admin_group'))
            Setting().set('azure_operator_group', request.form.get('azure_operator_group'))
            Setting().set('azure_user_group', request.form.get('azure_user_group'))
            result = {
                'status': True,
                'msg': 'Saved successfully. Please reload PDA to take effect.'
            }
        elif conf_type == 'oidc':
            Setting().set(
                'oidc_oauth_enabled',
                True if request.form.get('oidc_oauth_enabled') else False)
            Setting().set('oidc_oauth_key', request.form.get('oidc_oauth_key'))
            Setting().set('oidc_oauth_secret',
                          request.form.get('oidc_oauth_secret'))
            Setting().set('oidc_oauth_scope',
                          request.form.get('oidc_oauth_scope'))
            Setting().set('oidc_oauth_api_url',
                          request.form.get('oidc_oauth_api_url'))
            Setting().set('oidc_oauth_token_url',
                          request.form.get('oidc_oauth_token_url'))
            Setting().set('oidc_oauth_authorize_url',
                          request.form.get('oidc_oauth_authorize_url'))
            result = {
                'status': True,
                'msg': 'Saved successfully. Please reload PDA to take effect.'
            }
        else:
            return abort(400)

        return render_template('admin_setting_authentication.html',
                               result=result)


@admin_bp.route('/templates', methods=['GET', 'POST'])
@admin_bp.route('/templates/list', methods=['GET', 'POST'])
@login_required
@operator_role_required
def templates():
    templates = DomainTemplate.query.all()
    return render_template('template.html', templates=templates)


@admin_bp.route('/template/create', methods=['GET', 'POST'])
@login_required
@operator_role_required
def create_template():
    if request.method == 'GET':
        return render_template('template_add.html')
    if request.method == 'POST':
        try:
            name = request.form.getlist('name')[0]
            description = request.form.getlist('description')[0]

            if ' ' in name or not name or not type:
                flash("Please correct your input", 'error')
                return redirect(url_for('admin.create_template'))

            if DomainTemplate.query.filter(
                    DomainTemplate.name == name).first():
                flash(
                    "A template with the name {0} already exists!".format(
                        name), 'error')
                return redirect(url_for('admin.create_template'))

            t = DomainTemplate(name=name, description=description)
            result = t.create()
            if result['status'] == 'ok':
                history = History(msg='Add domain template {0}'.format(name),
                                  detail=str({
                                      'name': name,
                                      'description': description
                                  }),
                                  created_by=current_user.username)
                history.add()
                return redirect(url_for('admin.templates'))
            else:
                flash(result['msg'], 'error')
                return redirect(url_for('admin.create_template'))
        except Exception as e:
            current_app.logger.error(
                'Cannot create domain template. Error: {0}'.format(e))
            current_app.logger.debug(traceback.format_exc())
            abort(500)


@admin_bp.route('/template/create-from-zone', methods=['POST'])
@login_required
@operator_role_required
def create_template_from_zone():
    try:
        jdata = request.json
        name = jdata['name']
        description = jdata['description']
        domain_name = jdata['domain']

        if ' ' in name or not name or not type:
            return make_response(
                jsonify({
                    'status': 'error',
                    'msg': 'Please correct template name'
                }), 400)

        if DomainTemplate.query.filter(DomainTemplate.name == name).first():
            return make_response(
                jsonify({
                    'status':
                    'error',
                    'msg':
                    'A template with the name {0} already exists!'.format(name)
                }), 409)

        t = DomainTemplate(name=name, description=description)
        result = t.create()
        if result['status'] == 'ok':
            history = History(msg='Add domain template {0}'.format(name),
                              detail=str({
                                  'name': name,
                                  'description': description
                              }),
                              created_by=current_user.username)
            history.add()

            # After creating the domain in Domain Template in the,
            # local DB. We add records into it Record Template.
            records = []
            domain = Domain.query.filter(Domain.name == domain_name).first()
            if domain:
                # Query zone's rrsets from PowerDNS API
                rrsets = Record().get_rrsets(domain.name)
                if rrsets:
                    for r in rrsets:
                        name = '@' if r['name'] == domain_name + '.' else r[
                            'name'].replace('.{}.'.format(domain_name), '')
                        for record in r['records']:
                            t_record = DomainTemplateRecord(
                                name=name,
                                type=r['type'],
                                status=False if record['disabled'] else True,
                                ttl=r['ttl'],
                                data=record['content'])
                            records.append(t_record)

            result = t.replace_records(records)

            if result['status'] == 'ok':
                return make_response(
                    jsonify({
                        'status': 'ok',
                        'msg': result['msg']
                    }), 200)
            else:
                # Revert the domain template (remove it)
                # ff we cannot add records.
                t.delete_template()
                return make_response(
                    jsonify({
                        'status': 'error',
                        'msg': result['msg']
                    }), 500)

        else:
            return make_response(
                jsonify({
                    'status': 'error',
                    'msg': result['msg']
                }), 500)
    except Exception as e:
        current_app.logger.error(
            'Cannot create template from zone. Error: {0}'.format(e))
        current_app.logger.debug(traceback.format_exc())
        return make_response(
            jsonify({
                'status': 'error',
                'msg': 'Error when applying new changes'
            }), 500)


@admin_bp.route('/template/<path:template>/edit', methods=['GET'])
@login_required
@operator_role_required
def edit_template(template):
    try:
        t = DomainTemplate.query.filter(
            DomainTemplate.name == template).first()
        records_allow_to_edit = Setting().get_records_allow_to_edit()
        quick_edit = Setting().get('record_quick_edit')
        ttl_options = Setting().get_ttl_options()
        if t is not None:
            records = []
            for jr in t.records:
                if jr.type in records_allow_to_edit:
                    record = DomainTemplateRecord(
                        name=jr.name,
                        type=jr.type,
                        status='Active' if jr.status else 'Disabled',
                        ttl=jr.ttl,
                        data=jr.data,
                        comment=jr.comment if jr.comment else '')
                    records.append(record)

            return render_template('template_edit.html',
                                   template=t.name,
                                   records=records,
                                   editable_records=records_allow_to_edit,
                                   quick_edit=quick_edit,
                                   ttl_options=ttl_options)
    except Exception as e:
        current_app.logger.error(
            'Cannot open domain template page. DETAIL: {0}'.format(e))
        current_app.logger.debug(traceback.format_exc())
        abort(500)
    return redirect(url_for('admin.templates'))


@admin_bp.route('/template/<path:template>/apply',
                methods=['POST'],
                strict_slashes=False)
@login_required
def apply_records(template):
    try:
        jdata = request.json
        records = []

        for j in jdata['records']:
            name = '@' if j['record_name'] in ['@', ''] else j['record_name']
            type = j['record_type']
            data = j['record_data']
            comment = j['record_comment']
            status = 0 if j['record_status'] == 'Disabled' else 1
            ttl = int(j['record_ttl']) if j['record_ttl'] else 3600

            dtr = DomainTemplateRecord(name=name,
                                       type=type,
                                       data=data,
                                       comment=comment,
                                       status=status,
                                       ttl=ttl)
            records.append(dtr)

        t = DomainTemplate.query.filter(
            DomainTemplate.name == template).first()
        result = t.replace_records(records)
        if result['status'] == 'ok':
            jdata.pop('_csrf_token',
                      None)  # don't store csrf token in the history.
            history = History(
                msg='Apply domain template record changes to domain template {0}'
                .format(template),
                detail=str(json.dumps(jdata)),
                created_by=current_user.username)
            history.add()
            return make_response(jsonify(result), 200)
        else:
            return make_response(jsonify(result), 400)
    except Exception as e:
        current_app.logger.error(
            'Cannot apply record changes to the template. Error: {0}'.format(
                e))
        current_app.logger.debug(traceback.format_exc())
        return make_response(
            jsonify({
                'status': 'error',
                'msg': 'Error when applying new changes'
            }), 500)


@admin_bp.route('/template/<path:template>/delete', methods=['POST'])
@login_required
@operator_role_required
def delete_template(template):
    try:
        t = DomainTemplate.query.filter(
            DomainTemplate.name == template).first()
        if t is not None:
            result = t.delete_template()
            if result['status'] == 'ok':
                history = History(
                    msg='Deleted domain template {0}'.format(template),
                    detail=str({'name': template}),
                    created_by=current_user.username)
                history.add()
                return redirect(url_for('admin.templates'))
            else:
                flash(result['msg'], 'error')
                return redirect(url_for('admin.templates'))
    except Exception as e:
        current_app.logger.error(
            'Cannot delete template. Error: {0}'.format(e))
        current_app.logger.debug(traceback.format_exc())
        abort(500)
    return redirect(url_for('admin.templates'))


@admin_bp.route('/global-search', methods=['GET'])
@login_required
@operator_role_required
def global_search():
    if request.method == 'GET':
        domains = []
        records = []
        comments = []

        query = request.args.get('q')
        if query:
            server = Server(server_id='localhost')
            results = server.global_search(object_type='all', query=query)

            # Format the search result
            for result in results:
                if result['object_type'] == 'zone':
                    # Remove the dot at the end of string
                    result['name'] = result['name'][:-1]
                    domains.append(result)
                elif result['object_type'] == 'record':
                    # Remove the dot at the end of string
                    result['name'] = result['name'][:-1]
                    result['zone_id'] = result['zone_id'][:-1]
                    records.append(result)
                elif result['object_type'] == 'comment':
                    # Get the actual record name, exclude the domain part
                    result['name'] = result['name'].replace(result['zone_id'], '')
                    if result['name']:
                        result['name'] = result['name'][:-1]
                    else:
                        result['name'] = '@'
                    # Remove the dot at the end of string
                    result['zone_id'] = result['zone_id'][:-1]
                    comments.append(result)
                else:
                    pass

        return render_template('admin_global_search.html', domains=domains, records=records, comments=comments)
