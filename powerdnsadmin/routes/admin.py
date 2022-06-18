import json
import datetime
import traceback
import re
from base64 import b64encode
from ast import literal_eval
from flask import Blueprint, render_template, render_template_string, make_response, url_for, current_app, request, redirect, jsonify, abort, flash, session
from flask_login import login_required, current_user

from ..decorators import operator_role_required, admin_role_required, history_access_required
from ..models.user import User
from ..models.account import Account
from ..models.account_user import AccountUser
from ..models.role import Role
from ..models.server import Server
from ..models.setting import Setting
from ..models.history import History
from ..models.domain import Domain
from ..models.domain_user import DomainUser
from ..models.record import Record
from ..models.domain_template import DomainTemplate
from ..models.domain_template_record import DomainTemplateRecord
from ..models.api_key import ApiKey
from ..models.base import db

from ..lib.errors import ApiKeyCreateFail
from ..lib.schema import ApiPlainKeySchema

apikey_plain_schema = ApiPlainKeySchema(many=True)

admin_bp = Blueprint('admin',
                     __name__,
                     template_folder='templates',
                     url_prefix='/admin')

"""
changeSet is a list of tuples, in the following format
(old_state, new_state, change_type)

old_state: dictionary with "disabled" and "content" keys. {"disabled" : False, "content" : "1.1.1.1" }
new_state: similarly
change_type: "addition" or "deletion" or "status" for status change or "unchanged" for no change

Note: A change in "content", is considered a deletion and recreation of the same record,
holding the new content value.
"""
def get_record_changes(del_rrset, add_rrset):
    changeSet = []
    delSet = del_rrset['records'] if 'records' in del_rrset else []
    addSet = add_rrset['records'] if 'records' in add_rrset else []
    for d in delSet:  # get the deletions and status changes
        exists = False
        for a in addSet:
            if d['content'] == a['content']:
                exists = True
                if d['disabled'] != a['disabled']:
                    changeSet.append( ({"disabled":d['disabled'],"content":d['content']},
                                    {"disabled":a['disabled'],"content":a['content']},
                                    "status") )
                break

        if not exists: # deletion
            changeSet.append( ({"disabled":d['disabled'],"content":d['content']},
                            None,
                            "deletion") )

    for a in addSet:  # get the additions
        exists = False
        for d in delSet:
            if d['content'] == a['content']:
                exists = True
                # already checked for status change
                break
        if not exists:
            changeSet.append( (None, {"disabled":a['disabled'], "content":a['content']}, "addition") )
            continue

    for a in addSet:  # get the unchanged
        exists = False
        for c in changeSet:
            if c[1] != None and  c[1]["content"] == a['content']:
                exists = True
                break
        if not exists:
            changeSet.append( ( {"disabled":a['disabled'], "content":a['content']}, {"disabled":a['disabled'], "content":a['content']}, "unchanged") )

    return changeSet

# out_changes is a list of  HistoryRecordEntry objects in which we will append the new changes
# a HistoryRecordEntry represents a pair of add_rrset and del_rrset
def extract_changelogs_from_a_history_entry(out_changes, history_entry, change_num, record_name=None, record_type=None):

    if history_entry.detail is None:
        return

    if "add_rrsets" in history_entry.detail:
        detail_dict = json.loads(history_entry.detail)
    else: # not a record entry
        return

    add_rrsets = detail_dict['add_rrsets']
    del_rrsets = detail_dict['del_rrsets']


    for add_rrset in add_rrsets:
        exists = False
        for del_rrset in del_rrsets:
            if del_rrset['name'] == add_rrset['name'] and del_rrset['type'] == add_rrset['type']:
                exists = True
                if change_num not in out_changes:
                    out_changes[change_num] = []
                out_changes[change_num].append(HistoryRecordEntry(history_entry, del_rrset, add_rrset, "*"))
                break
        if not exists:  # this is a new record
            if change_num not in out_changes:
                out_changes[change_num] = []
            out_changes[change_num].append(HistoryRecordEntry(history_entry, [], add_rrset, "+"))  # (add_rrset, del_rrset, change_type)
    for del_rrset in del_rrsets:
        exists = False
        for add_rrset in add_rrsets:
            if del_rrset['name'] == add_rrset['name'] and del_rrset['type'] == add_rrset['type']:
                exists = True  # no need to add in the out_changes set
                break
        if not exists:  # this is a deletion
            if change_num not in out_changes:
                out_changes[change_num] = []
            out_changes[change_num].append(HistoryRecordEntry(history_entry, del_rrset, [], "-"))


    # only used for changelog per record
    if record_name != None and record_type != None: # then get only the records with the specific (record_name, record_type) tuple
        if change_num in out_changes:
            changes_i = out_changes[change_num]
        else:
            return
        for hre in changes_i: # for each history record entry in changes_i
            if 'type' in hre.add_rrset and hre.add_rrset['name'] == record_name and hre.add_rrset['type'] == record_type:
                continue
            elif 'type' in hre.del_rrset and hre.del_rrset['name'] == record_name and hre.del_rrset['type'] == record_type:
                continue
            else:
                out_changes[change_num].remove(hre)



# records with same (name,type) are considered as a single HistoryRecordEntry
# history_entry is of type History - used to extract created_by and created_on
# add_rrset is a dictionary of replace
# del_rrset is a dictionary of remove
class HistoryRecordEntry:
    def __init__(self, history_entry, del_rrset, add_rrset, change_type):
        # search the add_rrset index into the add_rrset set for the key (name, type)

        self.history_entry = history_entry
        self.add_rrset = add_rrset
        self.del_rrset = del_rrset
        self.change_type = change_type  # "*": edit or unchanged, "+" new tuple(name,type), "-" deleted (name,type) tuple
        self.changed_fields = []   # contains a subset of : [ttl, name, type]
        self.changeSet = []   # all changes for the records of this add_rrset-del_rrset pair


        if change_type == "+": # addition
            self.changed_fields.append("name")
            self.changed_fields.append("type")
            self.changed_fields.append("ttl")
            self.changeSet = get_record_changes(del_rrset, add_rrset)
        elif change_type == "-": # removal
            self.changed_fields.append("name")
            self.changed_fields.append("type")
            self.changed_fields.append("ttl")
            self.changeSet = get_record_changes(del_rrset, add_rrset)

        elif change_type == "*":  # edit of unchanged
            if add_rrset['ttl'] != del_rrset['ttl']:
                self.changed_fields.append("ttl")
            self.changeSet = get_record_changes(del_rrset, add_rrset)



    def toDict(self):
        return {
            "add_rrset" : self.add_rrset,
            "del_rrset" : self.del_rrset,
            "changed_fields" : self.changed_fields,
            "created_on" : self.history_entry.created_on,
            "created_by" : self.history_entry.created_by,
            "change_type" : self.change_type,
            "changeSet" : self.changeSet
        }

    def __eq__(self, obj2): # used for removal of objects from a list
        return True if obj2.toDict() == self.toDict() else False

@admin_bp.before_request
def before_request():
    # Manage session timeout
    session.permanent = True
    # current_app.permanent_session_lifetime = datetime.timedelta(
    #     minutes=int(Setting().get('session_timeout')))
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
            user_username = fdata.get('username', '').strip()

        user = User(username=user_username,
                    plain_text_password=fdata.get('password', ''),
                    firstname=fdata.get('firstname', '').strip(),
                    lastname=fdata.get('lastname', '').strip(),
                    email=fdata.get('email', '').strip(),
                    reload_info=False)

        if create:
            if not fdata.get('password', ''):
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

@admin_bp.route('/key/edit/<key_id>', methods=['GET', 'POST'])
@admin_bp.route('/key/edit', methods=['GET', 'POST'])
@login_required
@operator_role_required
def edit_key(key_id=None):
    domains = Domain.query.all()
    accounts = Account.query.all()
    roles = Role.query.all()
    apikey = None
    create = True
    plain_key = None

    if key_id:
        apikey = ApiKey.query.filter(ApiKey.id == key_id).first()
        create = False

        if not apikey:
            return render_template('errors/404.html'), 404

    if request.method == 'GET':
        return render_template('admin_edit_key.html',
                               key=apikey,
                               domains=domains,
                               accounts=accounts,
                               roles=roles,
                               create=create)

    if request.method == 'POST':
        fdata = request.form
        description = fdata['description']
        role = fdata.getlist('key_role')[0]
        domain_list = fdata.getlist('key_multi_domain')
        account_list = fdata.getlist('key_multi_account')

        # Create new apikey
        if create:
            if role == "User":
                domain_obj_list = Domain.query.filter(Domain.name.in_(domain_list)).all()
                account_obj_list = Account.query.filter(Account.name.in_(account_list)).all()
            else:
                account_obj_list, domain_obj_list = [], []

            apikey = ApiKey(desc=description,
                            role_name=role,
                            domains=domain_obj_list,
                            accounts=account_obj_list)
            try:
                apikey.create()
            except Exception as e:
                current_app.logger.error('Error: {0}'.format(e))
                raise ApiKeyCreateFail(message='Api key create failed')

            plain_key = apikey_plain_schema.dump([apikey])[0]["plain_key"]
            plain_key = b64encode(plain_key.encode('utf-8')).decode('utf-8')
            history_message =  "Created API key {0}".format(apikey.id)

        # Update existing apikey
        else:
            try:
                if role != "User":
                    domain_list, account_list = [], []
                apikey.update(role,description,domain_list, account_list)
                history_message =  "Updated API key {0}".format(apikey.id)
            except Exception as e:
                current_app.logger.error('Error: {0}'.format(e))

        history = History(msg=history_message,
                          detail = json.dumps({
                                'key': apikey.id,
                                'role': apikey.role.name,
                                'description': apikey.description,
                                'domains': [domain.name for domain in apikey.domains],
                                'accounts': [a.name for a in apikey.accounts]
                            }),
                          created_by=current_user.username)
        history.add()

        return render_template('admin_edit_key.html',
                               key=apikey,
                               domains=domains,
                               accounts=accounts,
                               roles=roles,
                               create=create,
                               plain_key=plain_key)

@admin_bp.route('/manage-keys', methods=['GET', 'POST'])
@login_required
@operator_role_required
def manage_keys():
    if request.method == 'GET':
        try:
            apikeys = ApiKey.query.all()
        except Exception as e:
            current_app.logger.error('Error: {0}'.format(e))
            abort(500)

        return render_template('admin_manage_keys.html',
                                keys=apikeys)

    elif request.method == 'POST':
        jdata = request.json
        if jdata['action'] == 'delete_key':

            apikey = ApiKey.query.get(jdata['data'])
            try:
                history_apikey_id = apikey.id
                history_apikey_role = apikey.role.name
                history_apikey_description = apikey.description
                history_apikey_domains = [ domain.name for domain in apikey.domains]

                apikey.delete()
            except Exception as e:
                current_app.logger.error('Error: {0}'.format(e))

            current_app.logger.info('Delete API key {0}'.format(apikey.id))
            history = History(msg='Delete API key {0}'.format(apikey.id),
                              detail = json.dumps({
                                    'key': history_apikey_id,
                                    'role': history_apikey_role,
                                    'description': history_apikey_description,
                                    'domains': history_apikey_domains
                                }),
                              created_by=current_user.username)
            history.add()

            return make_response(
                        jsonify({
                            'status': 'ok',
                            'msg': 'Key has been removed.'
                        }), 200)

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
                                   account_user_ids=[],
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


class DetailedHistory():
    def __init__(self, history, change_set):
        self.history = history
        self.detailed_msg = ""
        self.change_set = change_set

        if not history.detail:
            self.detailed_msg = ""
            return

        detail_dict = json.loads(history.detail)

        if 'domain_type' in detail_dict and 'account_id' in detail_dict:  # this is a domain creation
            self.detailed_msg = render_template_string("""
                    <table class="table table-bordered table-striped">
                        <tr><td>Domain type:</td><td>{{ domaintype }}</td></tr>
                        <tr><td>Account:</td><td>{{ account }}</td></tr>
                    </table>
                """,
                domaintype=detail_dict['domain_type'],
                account=Account.get_name_by_id(self=None, account_id=detail_dict['account_id']) if detail_dict['account_id'] != "0" else "None")

        elif 'authenticator' in detail_dict: # this is a user authentication
            self.detailed_msg = render_template_string("""
                <table class="table table-bordered table-striped" style="width:565px;">
                    <thead>
                        <tr>
                            <th colspan="3" style="background: rgba({{ background_rgba }});">
                                <p style="color:white;">User {{ username }} authentication {{ auth_result }}</p>
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Authenticator Type:</td>
                            <td colspan="2">{{ authenticator }}</td>
                        </tr>
                        <tr>
                            <td>IP Address</td>
                            <td colspan="2">{{ ip_address }}</td>
                        </tr>
                    </tbody>
                </table>
                """,
                background_rgba="68,157,68" if detail_dict['success'] == 1 else "201,48,44",
                username=detail_dict['username'],
                auth_result="success" if detail_dict['success'] == 1 else "failure",
                authenticator=detail_dict['authenticator'],
                ip_address=detail_dict['ip_address'])

        elif 'add_rrsets' in detail_dict: # this is a domain record change
            # changes_set = []
            self.detailed_msg = ""
            # extract_changelogs_from_a_history_entry(changes_set, history, 0)

        elif 'name' in detail_dict and 'template' in history.msg: # template creation / deletion
            self.detailed_msg = render_template_string("""
                <table class="table table-bordered table-striped">
                    <tr><td>Template name:</td><td>{{ template_name }}</td></tr>
                    <tr><td>Description:</td><td>{{ description }}</td></tr>
                </table>
                """,
                template_name=DetailedHistory.get_key_val(detail_dict, "name"),
                description=DetailedHistory.get_key_val(detail_dict, "description"))

        elif 'Change domain' in history.msg and 'access control' in history.msg: # added or removed a user from a domain
            users_with_access = DetailedHistory.get_key_val(detail_dict, "user_has_access")
            self.detailed_msg = render_template_string("""
                <table class="table table-bordered table-striped">
                    <tr><td>Users with access to this domain</td><td>{{ users_with_access }}</td></tr>
                    <tr><td>Number of users:</td><td>{{ users_with_access | length }}</td><tr>
                </table>
                """,
                users_with_access=users_with_access)

        elif 'Created API key' in history.msg or 'Updated API key' in history.msg:
            self.detailed_msg = render_template_string("""
                <table class="table table-bordered table-striped">
                    <tr><td>Key: </td><td>{{ keyname }}</td></tr>
                    <tr><td>Role:</td><td>{{ rolename }}</td></tr>
                    <tr><td>Description:</td><td>{{ description }}</td></tr>
                    <tr><td>Accessible domains with this API key:</td><td>{{ linked_domains }}</td></tr>
                    <tr><td>Accessible accounts with this API key:</td><td>{{ linked_accounts }}</td></tr>
                </table>
                """,
                keyname=DetailedHistory.get_key_val(detail_dict, "key"),
                rolename=DetailedHistory.get_key_val(detail_dict, "role"),
                description=DetailedHistory.get_key_val(detail_dict, "description"),
                linked_domains=DetailedHistory.get_key_val(detail_dict, "domains" if "domains" in detail_dict else "domain_acl"),
                linked_accounts=DetailedHistory.get_key_val(detail_dict, "accounts"))

        elif 'Delete API key' in history.msg:
            self.detailed_msg = render_template_string("""
                <table class="table table-bordered table-striped">
                    <tr><td>Key: </td><td>{{ keyname }}</td></tr>
                    <tr><td>Role:</td><td>{{ rolename }}</td></tr>
                    <tr><td>Description:</td><td>{{ description }}</td></tr>
                    <tr><td>Accessible domains with this API key:</td><td>{{ linked_domains }}</td></tr>
                </table>
                """,
                keyname=DetailedHistory.get_key_val(detail_dict, "key"),
                rolename=DetailedHistory.get_key_val(detail_dict, "role"),
                description=DetailedHistory.get_key_val(detail_dict, "description"),
                linked_domains=DetailedHistory.get_key_val(detail_dict, "domains"))

        elif 'Update type for domain' in history.msg:
            self.detailed_msg = render_template_string("""
                <table class="table table-bordered table-striped">
                    <tr><td>Domain: </td><td>{{ domain }}</td></tr>
                    <tr><td>Domain type:</td><td>{{ domain_type }}</td></tr>
                    <tr><td>Masters:</td><td>{{ masters }}</td></tr>
                </table>
                """,
                domain=DetailedHistory.get_key_val(detail_dict, "domain"),
                domain_type=DetailedHistory.get_key_val(detail_dict, "type"),
                masters=DetailedHistory.get_key_val(detail_dict, "masters"))

        elif 'reverse' in history.msg:
            self.detailed_msg = render_template_string("""
                <table class="table table-bordered table-striped">
                    <tr><td>Domain Type: </td><td>{{ domain_type }}</td></tr>
                    <tr><td>Domain Master IPs:</td><td>{{ domain_master_ips }}</td></tr>
                </table>
                """,
                domain_type=DetailedHistory.get_key_val(detail_dict, "domain_type"),
                domain_master_ips=DetailedHistory.get_key_val(detail_dict, "domain_master_ips"))

        elif DetailedHistory.get_key_val(detail_dict, 'msg') and DetailedHistory.get_key_val(detail_dict, 'status'):
            self.detailed_msg = render_template_string('''
                <table class="table table-bordered table-striped">
                    <tr><td>Status: </td><td>{{ history_status }}</td></tr>
                    <tr><td>Message:</td><td>{{ history_msg }}</td></tr>
                </table>
                ''',
                history_status=DetailedHistory.get_key_val(detail_dict, 'status'),
                history_msg=DetailedHistory.get_key_val(detail_dict, 'msg'))

    # check for lower key as well for old databases
    @staticmethod
    def get_key_val(_dict, key):
        return str(_dict.get(key, _dict.get(key.title(), '')))


# convert a list of History objects into DetailedHistory objects
def convert_histories(histories):
	changes_set = dict()
	detailedHistories = []
	j = 0
	for i in range(len(histories)):
		if histories[i].detail and ('add_rrsets' in histories[i].detail or 'del_rrsets' in histories[i].detail):
			extract_changelogs_from_a_history_entry(changes_set, histories[i], j)
			if j in changes_set:
				detailedHistories.append(DetailedHistory(histories[i], changes_set[j]))
			else: # no changes were found
				detailedHistories.append(DetailedHistory(histories[i], None))
			j += 1

		else:
			detailedHistories.append(DetailedHistory(histories[i], None))
	return detailedHistories

@admin_bp.route('/history', methods=['GET', 'POST'])
@login_required
@history_access_required
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
		doms = accounts = users = ""
		if current_user.role.name in [ 'Administrator', 'Operator']:
			all_domain_names = Domain.query.all()
			all_account_names = Account.query.all()
			all_user_names = User.query.all()



			for d in all_domain_names:
				doms += d.name + " "
			for acc in all_account_names:
				accounts += acc.name + " "
			for usr in all_user_names:
				users += usr.username + " "
		else: # special autocomplete for users
			all_domain_names = db.session.query(Domain) \
				.outerjoin(DomainUser, Domain.id == DomainUser.domain_id) \
				.outerjoin(Account, Domain.account_id == Account.id) \
				.outerjoin(AccountUser, Account.id == AccountUser.account_id) \
				.filter(
				db.or_(
					DomainUser.user_id == current_user.id,
					AccountUser.user_id == current_user.id
				)).all()

			all_account_names = db.session.query(Account) \
				.outerjoin(Domain, Domain.account_id == Account.id) \
				.outerjoin(DomainUser, Domain.id == DomainUser.domain_id) \
				.outerjoin(AccountUser, Account.id == AccountUser.account_id) \
				.filter(
				db.or_(
					DomainUser.user_id == current_user.id,
					AccountUser.user_id == current_user.id
				)).all()


			all_user_names = []
			for a in all_account_names:
				temp =  db.session.query(User) \
						.join(AccountUser, AccountUser.user_id == User.id) \
						.outerjoin(Account, Account.id == AccountUser.account_id) \
						.filter(
							db.or_(
								Account.id == a.id,
								AccountUser.account_id == a.id
							)
						) \
						.all()
				for u in temp:
					if u in all_user_names:
						continue
					all_user_names.append(u)

			for d in all_domain_names:
				doms += d.name + " "

			for a in all_account_names:
				accounts += a.name + " "
			for u in all_user_names:
				users += u.username + " "
		return render_template('admin_history.html', all_domain_names=doms, all_account_names=accounts, all_usernames=users)

# local_offset is the offset of the utc to the local time
# offset must be int
# return the date converted and simplified
def from_utc_to_local(local_offset, timeframe):
	offset = str(local_offset *(-1))
	date_split = str(timeframe).split(".")[0]
	date_converted = datetime.datetime.strptime(date_split, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(minutes=int(offset))
	return date_converted

@admin_bp.route('/history_table', methods=['GET', 'POST'])
@login_required
@history_access_required
def history_table():    # ajax call data

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

	detailedHistories = []
	lim = int(Setting().get('max_history_records'))  # max num of records

	if request.method == 'GET':
		if current_user.role.name in [ 'Administrator', 'Operator' ]:
			base_query = History.query
		else:
			# if the user isn't an administrator or operator,
			# allow_user_view_history must be enabled to get here,
			# so include history for the domains for the user
			base_query = db.session.query(History) \
				.join(Domain, History.domain_id == Domain.id) \
				.outerjoin(DomainUser, Domain.id == DomainUser.domain_id) \
				.outerjoin(Account, Domain.account_id == Account.id) \
				.outerjoin(AccountUser, Account.id == AccountUser.account_id) \
				.filter(
				db.or_(
					DomainUser.user_id == current_user.id,
					AccountUser.user_id == current_user.id
				))

		domain_name = request.args.get('domain_name_filter') if request.args.get('domain_name_filter') != None \
															and len(request.args.get('domain_name_filter')) != 0 else None
		account_name = request.args.get('account_name_filter') if request.args.get('account_name_filter') != None \
															and len(request.args.get('account_name_filter')) != 0 else None
		user_name = request.args.get('auth_name_filter') if request.args.get('auth_name_filter') != None \
															and len(request.args.get('auth_name_filter')) != 0 else None

		min_date = request.args.get('min') if request.args.get('min') != None and len( request.args.get('min')) != 0 else None
		if min_date != None:    # get 1 day earlier, to check for timezone errors
			min_date = str(datetime.datetime.strptime(min_date, '%Y-%m-%d') - datetime.timedelta(days=1))
		max_date = request.args.get('max') if request.args.get('max') != None and len( request.args.get('max')) != 0 else None
		if max_date != None:    # get 1 day later, to check for timezone errors
			max_date = str(datetime.datetime.strptime(max_date, '%Y-%m-%d') + datetime.timedelta(days=1))
		tzoffset = request.args.get('tzoffset') if request.args.get('tzoffset') != None and len(request.args.get('tzoffset')) != 0 else None
		changed_by = request.args.get('user_name_filter') if  request.args.get('user_name_filter') != None \
															and len(request.args.get('user_name_filter')) != 0 else None
		"""
			Auth methods: LOCAL, Github OAuth, Azure OAuth, SAML, OIDC OAuth, Google OAuth
		"""
		auth_methods = []
		if (request.args.get('auth_local_only_checkbox') is None \
														and request.args.get('auth_oauth_only_checkbox') is None \
														and request.args.get('auth_saml_only_checkbox') is None and request.args.get('auth_all_checkbox') is None):
			auth_methods = []
		if request.args.get('auth_all_checkbox') == "on":
			auth_methods.append("")
		if request.args.get('auth_local_only_checkbox') == "on":
			auth_methods.append("LOCAL")
		if request.args.get('auth_oauth_only_checkbox') == "on":
			auth_methods.append("OAuth")
		if request.args.get('auth_saml_only_checkbox') == "on":
			auth_methods.append("SAML")

		if request.args.get('domain_changelog_only_checkbox') != None:
			changelog_only = True if request.args.get('domain_changelog_only_checkbox') == "on" else False
		else:
			changelog_only = False




		# users cannot search for authentication
		if user_name != None and current_user.role.name not in [ 'Administrator', 'Operator']:
			histories = []
		elif domain_name != None:

			if not changelog_only:
				histories = base_query \
				.filter(
					db.and_(
						db.or_(
							History.msg.like("%domain "+ domain_name) if domain_name != "*" else History.msg.like("%domain%"),
							History.msg.like("%domain "+ domain_name + " access control") if domain_name != "*" else History.msg.like("%domain%access control")
						),
						History.created_on <= max_date  if max_date != None else True,
						History.created_on >= min_date if min_date != None else True,
						History.created_by == changed_by if changed_by != None else True
					)
				).order_by(History.created_on.desc()).limit(lim).all()
			else:
				# search for records changes only
				histories = base_query \
							.filter(
								db.and_(
									History.msg.like("Apply record changes to domain " + domain_name) if domain_name != "*" \
																			else History.msg.like("Apply record changes to domain%"),
									History.created_on <= max_date  if max_date != None else True,
									History.created_on >= min_date if min_date != None else True,
									History.created_by == changed_by if changed_by != None else True

								)
							).order_by(History.created_on.desc()) \
							.limit(lim).all()
		elif account_name != None:
			if current_user.role.name in ['Administrator', 'Operator']:
				histories = base_query \
					.join(Domain, History.domain_id == Domain.id) \
					.outerjoin(Account, Domain.account_id == Account.id) \
					.filter(
						db.and_(
							Account.id == Domain.account_id,
							account_name == Account.name if account_name != "*" else True,
							History.created_on <= max_date if max_date != None else True,
							History.created_on >= min_date if min_date != None else True,
							History.created_by == changed_by if changed_by != None else True
						)
					).order_by(History.created_on.desc()) \
					.limit(lim).all()
			else:
				histories = base_query \
							.filter(
								db.and_(
									Account.id == Domain.account_id,
									account_name == Account.name if account_name != "*" else True,
									History.created_on <= max_date if max_date != None else True,
									History.created_on >= min_date if min_date != None else True,
									History.created_by == changed_by if changed_by != None else True
								)
							).order_by(History.created_on.desc()) \
							.limit(lim).all()
		elif user_name != None and current_user.role.name in [ 'Administrator', 'Operator']: # only admins can see the user login-logouts

			histories = History.query \
					.filter(
						db.and_(
							db.or_(
								History.msg.like("User "+ user_name + " authentication%") if user_name != "*" and user_name != None else History.msg.like("%authentication%"),
								History.msg.like("User "+ user_name + " was not authorized%") if user_name != "*" and user_name != None else History.msg.like("User%was not authorized%")
							),
							History.created_on <= max_date if max_date != None else True,
							History.created_on >= min_date if min_date != None else True,
							History.created_by == changed_by if changed_by != None else True
						)
					) \
					.order_by(History.created_on.desc()).limit(lim).all()
			temp = []
			for h in histories:
				for method in auth_methods:
					if method in h.detail:
						temp.append(h)
						break
			histories = temp
		elif (changed_by != None or max_date != None) and current_user.role.name in [ 'Administrator', 'Operator'] :   # select changed by and date filters only
			histories = History.query \
					.filter(
						db.and_(
							History.created_on <= max_date  if max_date != None else True,
							History.created_on >= min_date if min_date != None else True,
							History.created_by == changed_by if changed_by != None else True
						)
					) \
					.order_by(History.created_on.desc()).limit(lim).all()
		elif (changed_by != None or max_date != None): # special filtering for user because one user does not have access to log-ins logs
			histories = base_query \
					.filter(
						db.and_(
							History.created_on <= max_date if max_date != None else True,
							History.created_on >= min_date if min_date != None else True,
							History.created_by == changed_by if changed_by != None else True
						)
					) \
					.order_by(History.created_on.desc()).limit(lim).all()
		elif max_date != None:  # if changed by == null and only date is applied
			histories = base_query.filter(
							db.and_(
								History.created_on <= max_date if max_date != None else True,
								History.created_on >= min_date if min_date != None else True,
							)
			).order_by(History.created_on.desc()).limit(lim).all()
		else:  # default view
			if current_user.role.name in [ 'Administrator', 'Operator']:
				histories = History.query.order_by(History.created_on.desc()).limit(lim).all()
			else:
				histories = db.session.query(History) \
					.join(Domain, History.domain_id == Domain.id) \
					.outerjoin(DomainUser, Domain.id == DomainUser.domain_id) \
					.outerjoin(Account, Domain.account_id == Account.id) \
					.outerjoin(AccountUser, Account.id == AccountUser.account_id) \
					.order_by(History.created_on.desc()) \
					.filter(
					db.or_(
						DomainUser.user_id == current_user.id,
						AccountUser.user_id == current_user.id
					)).limit(lim).all()

		detailedHistories = convert_histories(histories)

		# Remove dates from previous or next day that were brought over
		if tzoffset != None:
			if min_date != None:
				min_date_split = min_date.split()[0]
			if max_date != None:
				max_date_split = max_date.split()[0]
			for i, history_rec in enumerate(detailedHistories):
				local_date = str(from_utc_to_local(int(tzoffset), history_rec.history.created_on).date())
				if (min_date != None and local_date == min_date_split) or (max_date != None and local_date == max_date_split):
					detailedHistories[i] = None

		# Remove elements previously flagged as None
		detailedHistories = [h for h in detailedHistories if h is not None]

		return render_template('admin_history_table.html', histories=detailedHistories, len_histories=len(detailedHistories), lim=lim)



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
            'allow_user_create_domain', 'allow_user_remove_domain', 'allow_user_view_history', 'bg_domain_updates', 'site_name',
            'session_timeout', 'warn_session_timeout', 'ttl_options',
            'pdns_api_timeout', 'verify_ssl_connections', 'verify_user_email',
            'delete_sso_accounts', 'otp_field_enabled', 'custom_css', 'enable_api_rr_history', 'max_history_records', 'otp_force',
            'deny_domain_override', 'enforce_api_ttl', 'account_name_extra_chars'
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


def has_an_auth_method(local_db_enabled=None,
                       ldap_enabled=None,
                       google_oauth_enabled=None,
                       github_oauth_enabled=None,
                       oidc_oauth_enabled=None,
                       azure_oauth_enabled=None):
    if local_db_enabled is None:
        local_db_enabled = Setting().get('local_db_enabled')
    if ldap_enabled is None:
        ldap_enabled = Setting().get('ldap_enabled')
    if google_oauth_enabled is None:
        google_oauth_enabled = Setting().get('google_oauth_enabled')
    if github_oauth_enabled is None:
        github_oauth_enabled = Setting().get('github_oauth_enabled')
    if oidc_oauth_enabled is None:
        oidc_oauth_enabled = Setting().get('oidc_oauth_enabled')
    if azure_oauth_enabled is None:
        azure_oauth_enabled = Setting().get('azure_oauth_enabled')
    return local_db_enabled or ldap_enabled or google_oauth_enabled or github_oauth_enabled or oidc_oauth_enabled or azure_oauth_enabled


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

            if not has_an_auth_method(local_db_enabled=local_db_enabled):
                result = {
                    'status':
                    False,
                    'msg':
                    'Must have at least one authentication method enabled.'
                }
            else:
                Setting().set('local_db_enabled', local_db_enabled)
                Setting().set('signup_enabled', signup_enabled)
                result = {'status': True, 'msg': 'Saved successfully'}
        elif conf_type == 'ldap':
            ldap_enabled = True if request.form.get('ldap_enabled') else False

            if not has_an_auth_method(ldap_enabled=ldap_enabled):
                result = {
                    'status':
                        False,
                    'msg':
                        'Must have at least one authentication method enabled.'
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
                Setting().set(
                    'autoprovisioning', True
                    if request.form.get('autoprovisioning') == 'ON' else False)
                Setting().set('autoprovisioning_attribute',
                              request.form.get('autoprovisioning_attribute'))

                if request.form.get('autoprovisioning')=='ON':
                    if  validateURN(request.form.get('urn_value')):
                        Setting().set('urn_value',
                                       request.form.get('urn_value'))
                    else:
                        return render_template('admin_setting_authentication.html',
                                    error="Invalid urn")
                else:
                    Setting().set('urn_value',
                                       request.form.get('urn_value'))

                Setting().set('purge', True
                    if request.form.get('purge') == 'ON' else False)


                result = {'status': True, 'msg': 'Saved successfully'}
        elif conf_type == 'google':
            google_oauth_enabled = True if request.form.get(
                'google_oauth_enabled') else False
            if not has_an_auth_method(google_oauth_enabled=google_oauth_enabled):
                result = {
                    'status':
                        False,
                    'msg':
                        'Must have at least one authentication method enabled.'
                }
            else:
                Setting().set('google_oauth_enabled', google_oauth_enabled)
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
                    'msg':
                    'Saved successfully. Please reload PDA to take effect.'
                }
        elif conf_type == 'github':
            github_oauth_enabled = True if request.form.get(
                'github_oauth_enabled') else False
            if not has_an_auth_method(github_oauth_enabled=github_oauth_enabled):
                result = {
                    'status':
                        False,
                    'msg':
                        'Must have at least one authentication method enabled.'
                }
            else:
                Setting().set('github_oauth_enabled', github_oauth_enabled)
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
                    'msg':
                    'Saved successfully. Please reload PDA to take effect.'
                }
        elif conf_type == 'azure':
            azure_oauth_enabled = True if request.form.get(
                'azure_oauth_enabled') else False
            if not has_an_auth_method(azure_oauth_enabled=azure_oauth_enabled):
                result = {
                    'status':
                        False,
                    'msg':
                        'Must have at least one authentication method enabled.'
                }
            else:
                Setting().set('azure_oauth_enabled', azure_oauth_enabled)
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
                Setting().set(
                    'azure_sg_enabled', True
                    if request.form.get('azure_sg_enabled') == 'ON' else False)
                Setting().set('azure_admin_group',
                              request.form.get('azure_admin_group'))
                Setting().set('azure_operator_group',
                              request.form.get('azure_operator_group'))
                Setting().set('azure_user_group',
                              request.form.get('azure_user_group'))
                Setting().set(
                    'azure_group_accounts_enabled', True
                    if request.form.get('azure_group_accounts_enabled') == 'ON' else False)
                Setting().set('azure_group_accounts_name',
                              request.form.get('azure_group_accounts_name'))
                Setting().set('azure_group_accounts_name_re',
                              request.form.get('azure_group_accounts_name_re'))
                Setting().set('azure_group_accounts_description',
                              request.form.get('azure_group_accounts_description'))
                Setting().set('azure_group_accounts_description_re',
                              request.form.get('azure_group_accounts_description_re'))
                result = {
                    'status': True,
                    'msg':
                    'Saved successfully. Please reload PDA to take effect.'
                }
        elif conf_type == 'oidc':
            oidc_oauth_enabled = True if request.form.get(
                'oidc_oauth_enabled') else False
            if not has_an_auth_method(oidc_oauth_enabled=oidc_oauth_enabled):
                result = {
                    'status':
                        False,
                    'msg':
                        'Must have at least one authentication method enabled.'
                }
            else:
                Setting().set(
                    'oidc_oauth_enabled',
                    True if request.form.get('oidc_oauth_enabled') else False)
                Setting().set('oidc_oauth_key',
                              request.form.get('oidc_oauth_key'))
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
                Setting().set('oidc_oauth_logout_url',
                              request.form.get('oidc_oauth_logout_url'))
                Setting().set('oidc_oauth_username',
                              request.form.get('oidc_oauth_username'))
                Setting().set('oidc_oauth_firstname',
                              request.form.get('oidc_oauth_firstname'))
                Setting().set('oidc_oauth_last_name',
                              request.form.get('oidc_oauth_last_name'))
                Setting().set('oidc_oauth_email',
                              request.form.get('oidc_oauth_email'))
                Setting().set('oidc_oauth_account_name_property',
                              request.form.get('oidc_oauth_account_name_property'))
                Setting().set('oidc_oauth_account_description_property',
                              request.form.get('oidc_oauth_account_description_property'))
                result = {
                    'status': True,
                    'msg':
                    'Saved successfully. Please reload PDA to take effect.'
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
                                  detail = json.dumps({
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
                              detail = json.dumps({
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
                detail = json.dumps(jdata),
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
                    detail = json.dumps({'name': template}),
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

def validateURN(value):
    NID_PATTERN = re.compile(r'^[0-9a-z][0-9a-z-]{1,31}$', flags=re.IGNORECASE)
    NSS_PCHAR = '[a-z0-9-._~]|%[a-f0-9]{2}|[!$&\'()*+,;=]|:|@'
    NSS_PATTERN = re.compile(fr'^({NSS_PCHAR})({NSS_PCHAR}|/|\?)*$', re.IGNORECASE)

    prefix=value.split(':')
    if (len(prefix)<3):
        current_app.logger.warning( "Too small urn prefix" )
        return False

    urn=prefix[0]
    nid=prefix[1]
    nss=value.replace(urn+":"+nid+":", "")

    if not urn.lower()=="urn":
        current_app.logger.warning( urn + ' contains invalid characters ' )
        return False
    if not re.match(NID_PATTERN, nid.lower()):
        current_app.logger.warning( nid + ' contains invalid characters ' )
        return False
    if not re.match(NSS_PATTERN, nss):
        current_app.logger.warning( nss + ' contains invalid characters ' )
        return False

    return True
