import re
import json
import datetime
import traceback
import dns.name
import dns.reversename
from distutils.version import StrictVersion
from flask import Blueprint, render_template, make_response, url_for, current_app, request, redirect, abort, jsonify, g, session
from flask_login import login_required, current_user, login_manager

from ..lib.utils import pretty_json
from ..decorators import can_create_domain, operator_role_required, can_access_domain, can_configure_dnssec
from ..models.user import User, Anonymous
from ..models.account import Account
from ..models.setting import Setting
from ..models.history import History
from ..models.domain import Domain
from ..models.record import Record
from ..models.record_entry import RecordEntry
from ..models.domain_template import DomainTemplate
from ..models.domain_template_record import DomainTemplateRecord
from ..models.domain_setting import DomainSetting

domain_bp = Blueprint('domain',
                      __name__,
                      template_folder='templates',
                      url_prefix='/domain')


@domain_bp.before_request
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


@domain_bp.route('/<path:domain_name>', methods=['GET'])
@login_required
@can_access_domain
def domain(domain_name):
    # Validate the domain existing in the local DB
    domain = Domain.query.filter(Domain.name == domain_name).first()
    if not domain:
        abort(404)

    # Query domain's rrsets from PowerDNS API
    rrsets = Record().get_rrsets(domain.name)
    current_app.logger.debug("Fetched rrests: \n{}".format(pretty_json(rrsets)))

    # API server might be down, misconfigured
    if not rrsets and domain.type != 'Slave':
        abort(500)

    quick_edit = Setting().get('record_quick_edit')
    records_allow_to_edit = Setting().get_records_allow_to_edit()
    forward_records_allow_to_edit = Setting(
    ).get_forward_records_allow_to_edit()
    reverse_records_allow_to_edit = Setting(
    ).get_reverse_records_allow_to_edit()
    ttl_options = Setting().get_ttl_options()
    records = []

    # Render the "records" to display in HTML datatable
    #
    # BUG: If we have multiple records with the same name
    # and each record has its own comment, the display of
    # [record-comment] may not consistent because PDNS API
    # returns the rrsets (records, comments) has different
    # order than its database records.
    # TODO:
    #   - Find a way to make it consistent, or
    #   - Only allow one comment for that case
    if StrictVersion(Setting().get('pdns_version')) >= StrictVersion('4.0.0'):
        for r in rrsets:
            if r['type'] in records_allow_to_edit:
                r_name = r['name'].rstrip('.')

                # If it is reverse zone and pretty_ipv6_ptr setting
                # is enabled, we reformat the name for ipv6 records.
                if Setting().get('pretty_ipv6_ptr') and r[
                        'type'] == 'PTR' and 'ip6.arpa' in r_name:
                    r_name = dns.reversename.to_address(
                        dns.name.from_text(r_name))

                # Create the list of records in format that
                # PDA jinja2 template can understand.
                index = 0
                for record in r['records']:
                    if (len(r['comments'])>index):
                        c=r['comments'][index]['content']
                    else:
                        c=''
                    record_entry = RecordEntry(
                        name=r_name,
                        type=r['type'],
                        status='Disabled' if record['disabled'] else 'Active',
                        ttl=r['ttl'],
                        data=record['content'],
                        comment=c,
                        is_allowed_edit=True)
                    index += 1
                    records.append(record_entry)
    else:
        # Unsupported version
        abort(500)

    if not re.search(r'ip6\.arpa|in-addr\.arpa$', domain_name):
        editable_records = forward_records_allow_to_edit
    else:
        editable_records = reverse_records_allow_to_edit

    return render_template('domain.html',
                           domain=domain,
                           records=records,
                           editable_records=editable_records,
                           quick_edit=quick_edit,
                           ttl_options=ttl_options)


@domain_bp.route('/add', methods=['GET', 'POST'])
@login_required
@can_create_domain
def add():
    templates = DomainTemplate.query.all()
    if request.method == 'POST':
        try:
            domain_name = request.form.getlist('domain_name')[0]
            domain_type = request.form.getlist('radio_type')[0]
            domain_template = request.form.getlist('domain_template')[0]
            soa_edit_api = request.form.getlist('radio_type_soa_edit_api')[0]
            account_id = request.form.getlist('accountid')[0]

            if ' ' in domain_name or not domain_name or not domain_type:
                return render_template(
                    'errors/400.html',
                    msg="Please enter a valid domain name"), 400

            #TODO: Validate ip addresses input
            if domain_type == 'slave':
                if request.form.getlist('domain_master_address'):
                    domain_master_string = request.form.getlist(
                        'domain_master_address')[0]
                    domain_master_string = domain_master_string.replace(
                        ' ', '')
                    domain_master_ips = domain_master_string.split(',')
            else:
                domain_master_ips = []

            account_name = Account().get_name_by_id(account_id)

            d = Domain()
            result = d.add(domain_name=domain_name,
                           domain_type=domain_type,
                           soa_edit_api=soa_edit_api,
                           domain_master_ips=domain_master_ips,
                           account_name=account_name)
            if result['status'] == 'ok':
                history = History(msg='Add domain {0}'.format(domain_name),
                                  detail=str({
                                      'domain_type': domain_type,
                                      'domain_master_ips': domain_master_ips,
                                      'account_id': account_id
                                  }),
                                  created_by=current_user.username)
                history.add()

                # grant user access to the domain
                Domain(name=domain_name).grant_privileges([current_user.id])

                # apply template if needed
                if domain_template != '0':
                    template = DomainTemplate.query.filter(
                        DomainTemplate.id == domain_template).first()
                    template_records = DomainTemplateRecord.query.filter(
                        DomainTemplateRecord.template_id ==
                        domain_template).all()
                    record_data = []
                    for template_record in template_records:
                        record_row = {
                            'record_data': template_record.data,
                            'record_name': template_record.name,
                            'record_status': 'Active' if template_record.status else 'Disabled',
                            'record_ttl': template_record.ttl,
                            'record_type': template_record.type,
                            'comment_data': [{'content': template_record.comment, 'account': ''}]
                        }
                        record_data.append(record_row)
                    r = Record()
                    result = r.apply(domain_name, record_data)
                    if result['status'] == 'ok':
                        history = History(
                            msg='Applying template {0} to {1} successfully.'.
                            format(template.name, domain_name),
                            detail=str(
                                json.dumps({
                                    "domain":
                                    domain_name,
                                    "template":
                                    template.name,
                                    "add_rrests":
                                    result['data'][0]['rrsets'],
                                    "del_rrests":
                                    result['data'][1]['rrsets']
                                })),
                            created_by=current_user.username)
                        history.add()
                    else:
                        history = History(
                            msg=
                            'Failed to apply template {0} to {1}.'
                            .format(template.name, domain_name),
                            detail=str(result),
                            created_by=current_user.username)
                        history.add()
                return redirect(url_for('dashboard.dashboard'))
            else:
                return render_template('errors/400.html',
                                       msg=result['msg']), 400
        except Exception as e:
            current_app.logger.error('Cannot add domain. Error: {0}'.format(e))
            current_app.logger.debug(traceback.format_exc())
            abort(500)

    else:
        accounts = Account.query.all()
        return render_template('domain_add.html',
                               templates=templates,
                               accounts=accounts)


@domain_bp.route('/setting/<path:domain_name>/delete', methods=['POST'])
@login_required
@operator_role_required
def delete(domain_name):
    d = Domain()
    result = d.delete(domain_name)

    if result['status'] == 'error':
        abort(500)

    history = History(msg='Delete domain {0}'.format(domain_name),
                      created_by=current_user.username)
    history.add()

    return redirect(url_for('dashboard.dashboard'))


@domain_bp.route('/setting/<path:domain_name>/manage', methods=['GET', 'POST'])
@login_required
@operator_role_required
def setting(domain_name):
    if request.method == 'GET':
        domain = Domain.query.filter(Domain.name == domain_name).first()
        if not domain:
            abort(404)
        users = User.query.all()
        accounts = Account.query.all()

        # get list of user ids to initialize selection data
        d = Domain(name=domain_name)
        domain_user_ids = d.get_user()
        account = d.get_account()

        return render_template('domain_setting.html',
                               domain=domain,
                               users=users,
                               domain_user_ids=domain_user_ids,
                               accounts=accounts,
                               domain_account=account)

    if request.method == 'POST':
        # username in right column
        new_user_list = request.form.getlist('domain_multi_user[]')
        new_user_ids = [
            user.id for user in User.query.filter(
                User.username.in_(new_user_list)).all() if user
        ]

        # grant/revoke user privileges
        d = Domain(name=domain_name)
        d.grant_privileges(new_user_ids)

        history = History(
            msg='Change domain {0} access control'.format(domain_name),
            detail=str({'user_has_access': new_user_list}),
            created_by=current_user.username)
        history.add()

        return redirect(url_for('domain.setting', domain_name=domain_name))


@domain_bp.route('/setting/<path:domain_name>/change_type',
                 methods=['POST'])
@login_required
@operator_role_required
def change_type(domain_name):
    domain = Domain.query.filter(Domain.name == domain_name).first()
    if not domain:
        abort(404)
    domain_type = request.form.get('domain_type')
    if domain_type is None:
        abort(500)
    if domain_type == '0':
        return redirect(url_for('domain.setting', domain_name=domain_name))

    #TODO: Validate ip addresses input
    domain_master_ips = []
    if domain_type == 'slave' and request.form.getlist('domain_master_address'):
        domain_master_string = request.form.getlist(
            'domain_master_address')[0]
        domain_master_string = domain_master_string.replace(
            ' ', '')
        domain_master_ips = domain_master_string.split(',')

    d = Domain()
    status = d.update_kind(domain_name=domain_name,
                           kind=domain_type,
                           masters=domain_master_ips)
    if status['status'] == 'ok':
        history = History(msg='Update type for domain {0}'.format(domain_name),
                          detail=str({
                              "domain": domain_name,
                              "type": domain_type,
                              "masters": domain_master_ips
                          }),
                          created_by=current_user.username)
        history.add()
        return redirect(url_for('domain.setting', domain_name = domain_name))
    else:
        abort(500)


@domain_bp.route('/setting/<path:domain_name>/change_soa_setting',
                 methods=['POST'])
@login_required
@operator_role_required
def change_soa_edit_api(domain_name):
    domain = Domain.query.filter(Domain.name == domain_name).first()
    if not domain:
        abort(404)
    new_setting = request.form.get('soa_edit_api')
    if new_setting is None:
        abort(500)
    if new_setting == '0':
        return redirect(url_for('domain.setting', domain_name=domain_name))

    d = Domain()
    status = d.update_soa_setting(domain_name=domain_name,
                                  soa_edit_api=new_setting)
    if status['status'] == 'ok':
        history = History(
            msg='Update soa_edit_api for domain {0}'.format(domain_name),
            detail=str({
                "domain": domain_name,
                "soa_edit_api": new_setting
            }),
            created_by=current_user.username)
        history.add()
        return redirect(url_for('domain.setting', domain_name = domain_name))
    else:
        abort(500)


@domain_bp.route('/setting/<path:domain_name>/change_account',
                 methods=['POST'])
@login_required
@operator_role_required
def change_account(domain_name):
    domain = Domain.query.filter(Domain.name == domain_name).first()
    if not domain:
        abort(404)

    account_id = request.form.get('accountid')
    status = Domain(name=domain.name).assoc_account(account_id)
    if status['status']:
        return redirect(url_for('domain.setting', domain_name=domain.name))
    else:
        abort(500)


@domain_bp.route('/<path:domain_name>/apply',
                 methods=['POST'],
                 strict_slashes=False)
@login_required
@can_access_domain
def record_apply(domain_name):
    try:
        jdata = request.json
        submitted_serial = jdata['serial']
        submitted_record = jdata['record']
        domain = Domain.query.filter(Domain.name == domain_name).first()

        if domain:
            current_app.logger.debug('Current domain serial: {0}'.format(
                domain.serial))

            if int(submitted_serial) != domain.serial:
                return make_response(
                    jsonify({
                        'status':
                        'error',
                        'msg':
                        'The zone has been changed by another session or user. Please refresh this web page to load updated records.'
                    }), 500)
        else:
            return make_response(
                jsonify({
                    'status':
                    'error',
                    'msg':
                    'Domain name {0} does not exist'.format(domain_name)
                }), 404)

        r = Record()
        result = r.apply(domain_name, submitted_record)
        if result['status'] == 'ok':
            history = History(
                msg='Apply record changes to domain {0}'.format(domain_name),
                detail=str(
                    json.dumps({
                        "domain": domain_name,
                        "add_rrests": result['data'][0]['rrsets'],
                        "del_rrests": result['data'][1]['rrsets']
                    })),
                created_by=current_user.username)
            history.add()
            return make_response(jsonify(result), 200)
        else:
            return make_response(jsonify(result), 400)
    except Exception as e:
        current_app.logger.error(
            'Cannot apply record changes. Error: {0}'.format(e))
        current_app.logger.debug(traceback.format_exc())
        return make_response(
            jsonify({
                'status': 'error',
                'msg': 'Error when applying new changes'
            }), 500)


@domain_bp.route('/<path:domain_name>/update',
                 methods=['POST'],
                 strict_slashes=False)
@login_required
@can_access_domain
def record_update(domain_name):
    """
    This route is used for domain work as Slave Zone only
    Pulling the records update from its Master
    """
    try:
        jdata = request.json

        domain_name = jdata['domain']
        d = Domain()
        result = d.update_from_master(domain_name)
        if result['status'] == 'ok':
            return make_response(
                jsonify({
                    'status': 'ok',
                    'msg': result['msg']
                }), 200)
        else:
            return make_response(
                jsonify({
                    'status': 'error',
                    'msg': result['msg']
                }), 500)
    except Exception as e:
        current_app.logger.error('Cannot update record. Error: {0}'.format(e))
        current_app.logger.debug(traceback.format_exc())
        return make_response(
            jsonify({
                'status': 'error',
                'msg': 'Error when applying new changes'
            }), 500)


@domain_bp.route('/<path:domain_name>/info', methods=['GET'])
@login_required
@can_access_domain
def info(domain_name):
    domain = Domain()
    domain_info = domain.get_domain_info(domain_name)
    return make_response(jsonify(domain_info), 200)


@domain_bp.route('/<path:domain_name>/dnssec', methods=['GET'])
@login_required
@can_access_domain
def dnssec(domain_name):
    domain = Domain()
    dnssec = domain.get_domain_dnssec(domain_name)
    return make_response(jsonify(dnssec), 200)


@domain_bp.route('/<path:domain_name>/dnssec/enable', methods=['POST'])
@login_required
@can_access_domain
@can_configure_dnssec
def dnssec_enable(domain_name):
    domain = Domain()
    dnssec = domain.enable_domain_dnssec(domain_name)
    return make_response(jsonify(dnssec), 200)


@domain_bp.route('/<path:domain_name>/dnssec/disable', methods=['POST'])
@login_required
@can_access_domain
@can_configure_dnssec
def dnssec_disable(domain_name):
    domain = Domain()
    dnssec = domain.get_domain_dnssec(domain_name)

    for key in dnssec['dnssec']:
        domain.delete_dnssec_key(domain_name, key['id'])

    return make_response(jsonify({'status': 'ok', 'msg': 'DNSSEC removed.'}))


@domain_bp.route('/<path:domain_name>/manage-setting', methods=['GET', 'POST'])
@login_required
@operator_role_required
def admin_setdomainsetting(domain_name):
    if request.method == 'POST':
        #
        # post data should in format
        # {'action': 'set_setting', 'setting': 'default_action, 'value': 'True'}
        #
        try:
            jdata = request.json
            data = jdata['data']

            if jdata['action'] == 'set_setting':
                new_setting = data['setting']
                new_value = str(data['value'])
                domain = Domain.query.filter(
                    Domain.name == domain_name).first()
                setting = DomainSetting.query.filter(
                    DomainSetting.domain == domain).filter(
                        DomainSetting.setting == new_setting).first()

                if setting:
                    if setting.set(new_value):
                        history = History(
                            msg='Setting {0} changed value to {1} for {2}'.
                            format(new_setting, new_value, domain.name),
                            created_by=current_user.username)
                        history.add()
                        return make_response(
                            jsonify({
                                'status': 'ok',
                                'msg': 'Setting updated.'
                            }))
                    else:
                        return make_response(
                            jsonify({
                                'status': 'error',
                                'msg': 'Unable to set value of setting.'
                            }))
                else:
                    if domain.add_setting(new_setting, new_value):
                        history = History(
                            msg=
                            'New setting {0} with value {1} for {2} has been created'
                            .format(new_setting, new_value, domain.name),
                            created_by=current_user.username)
                        history.add()
                        return make_response(
                            jsonify({
                                'status': 'ok',
                                'msg': 'New setting created and updated.'
                            }))
                    else:
                        return make_response(
                            jsonify({
                                'status': 'error',
                                'msg': 'Unable to create new setting.'
                            }))
            else:
                return make_response(
                    jsonify({
                        'status': 'error',
                        'msg': 'Action not supported.'
                    }), 400)
        except Exception as e:
            current_app.logger.error(
                'Cannot change domain setting. Error: {0}'.format(e))
            current_app.logger.debug(traceback.format_exc())
            return make_response(
                jsonify({
                    'status':
                    'error',
                    'msg':
                    'There is something wrong, please contact Administrator.'
                }), 400)
