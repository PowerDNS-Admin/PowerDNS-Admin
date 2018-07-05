import base64
import json
import logging as logger
import os
import traceback
import re
from distutils.util import strtobool
from distutils.version import StrictVersion
from functools import wraps
from io import BytesIO

import jinja2
import qrcode as qrc
import qrcode.image.svg as qrc_svg
from flask import g, request, make_response, jsonify, render_template, session, redirect, url_for, send_from_directory, abort, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug import secure_filename
from werkzeug.security import gen_salt

from .models import User, Account, Domain, Record, Server, History, Anonymous, Setting, DomainSetting, DomainTemplate, DomainTemplateRecord
from app import app, login_manager, github, google
from app.lib import utils
from app.decorators import admin_role_required, can_access_domain, can_configure_dnssec

if app.config['SAML_ENABLED']:
    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    from onelogin.saml2.utils import OneLogin_Saml2_Utils

logging = logger.getLogger(__name__)

# FILTERS
app.jinja_env.filters['display_record_name'] = utils.display_record_name
app.jinja_env.filters['display_master_name'] = utils.display_master_name
app.jinja_env.filters['display_second_to_time'] = utils.display_time
app.jinja_env.filters['email_to_gravatar_url'] = utils.email_to_gravatar_url

# Flag for pdns v4.x.x
# TODO: Find another way to do this
PDNS_VERSION = app.config['PDNS_VERSION']
if StrictVersion(PDNS_VERSION) >= StrictVersion('4.0.0'):
    NEW_SCHEMA = True
else:
    NEW_SCHEMA = False


@app.context_processor
def inject_fullscreen_layout_setting():
    setting_value = Setting().get('fullscreen_layout')
    return dict(fullscreen_layout_setting=strtobool(setting_value))


@app.context_processor
def inject_record_helper_setting():
    setting_value = Setting().get('record_helper')
    return dict(record_helper_setting=strtobool(setting_value))


@app.context_processor
def inject_login_ldap_first_setting():
    setting_value = Setting().get('login_ldap_first')
    return dict(login_ldap_first_setting=strtobool(setting_value))


@app.context_processor
def inject_default_record_table_size_setting():
    setting_value = Setting().get('default_record_table_size')
    return dict(default_record_table_size_setting=setting_value)


@app.context_processor
def inject_default_domain_table_size_setting():
    setting_value = Setting().get('default_domain_table_size')
    return dict(default_domain_table_size_setting=setting_value)


@app.context_processor
def inject_auto_ptr_setting():
    setting_value = Setting().get('auto_ptr')
    return dict(auto_ptr_setting=strtobool(setting_value))


# START USER AUTHENTICATION HANDLER
@app.before_request
def before_request():
    # check site maintenance mode first
    maintenance = Setting().get('maintenance')
    if strtobool(maintenance):
        return render_template('maintenance.html')

    # check if user is anonymous
    g.user = current_user
    login_manager.anonymous_user = Anonymous


@login_manager.user_loader
def load_user(id):
    """
    This will be current_user
    """
    return User.query.get(int(id))

def dyndns_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated is False:
            return render_template('dyndns.html', response='badauth'), 200
        return f(*args, **kwargs)
    return decorated_function


@login_manager.request_loader
def login_via_authorization_header(request):
    auth_header = request.headers.get('Authorization')
    if auth_header:
        auth_header = auth_header.replace('Basic ', '', 1)
        try:
            auth_header = str(base64.b64decode(auth_header), 'utf-8')
            username,password = auth_header.split(":")
        except TypeError as e:
            return None
        user = User(username=username, password=password, plain_text_password=password)
        try:
            auth = user.is_validate(method='LOCAL', src_ip=request.remote_addr)
            if auth == False:
                return None
            else:
                login_user(user, remember = False)
                return user
        except:
            return None
    return None
# END USER AUTHENTICATION HANDLER


# START VIEWS
@app.errorhandler(400)
def http_bad_request(e):
    return redirect(url_for('error', code=400))


@app.errorhandler(401)
def http_unauthorized(e):
    return redirect(url_for('error', code=401))


@app.errorhandler(404)
def http_internal_server_error(e):
    return redirect(url_for('error', code=404))


@app.errorhandler(500)
def http_page_not_found(e):
    return redirect(url_for('error', code=500))


@app.route('/error/<path:code>')
def error(code, msg=None):
    supported_code = ('400', '401', '404', '500')
    if code in supported_code:
        return render_template('errors/{0}.html'.format(code), msg=msg), int(code)
    else:
        return render_template('errors/404.html'), 404


@app.route('/register', methods=['GET'])
def register():
    SIGNUP_ENABLED = app.config['SIGNUP_ENABLED']
    if SIGNUP_ENABLED:
        return render_template('register.html')
    else:
        return render_template('errors/404.html'), 404


@app.route('/google/login')
def google_login():
    if not app.config.get('GOOGLE_OAUTH_ENABLE'):
        return abort(400)
    return google.authorize(callback=url_for('authorized', _external=True))


@app.route('/github/login')
def github_login():
    if not app.config.get('GITHUB_OAUTH_ENABLE'):
        return abort(400)
    return github.authorize(callback=url_for('authorized', _external=True))

@app.route('/saml/login')
def saml_login():
    if not app.config.get('SAML_ENABLED'):
        return abort(400)
    req = utils.prepare_flask_request(request)
    auth = utils.init_saml_auth(req)
    redirect_url=OneLogin_Saml2_Utils.get_self_url(req) + url_for('saml_authorized')
    return redirect(auth.login(return_to=redirect_url))

@app.route('/saml/metadata')
def saml_metadata():
    if not app.config.get('SAML_ENABLED'):
        return abort(400)
    req = utils.prepare_flask_request(request)
    auth = utils.init_saml_auth(req)
    settings = auth.get_settings()
    metadata = settings.get_sp_metadata()
    errors = settings.validate_metadata(metadata)

    if len(errors) == 0:
        resp = make_response(metadata, 200)
        resp.headers['Content-Type'] = 'text/xml'
    else:
        resp = make_response(errors.join(', '), 500)
    return resp

@app.route('/saml/authorized', methods=['GET', 'POST'])
def saml_authorized():
    errors = []
    if not app.config.get('SAML_ENABLED'):
        return abort(400)
    req = utils.prepare_flask_request(request)
    auth = utils.init_saml_auth(req)
    auth.process_response()
    errors = auth.get_errors()
    if len(errors) == 0:
        session['samlUserdata'] = auth.get_attributes()
        session['samlNameId'] = auth.get_nameid()
        session['samlSessionIndex'] = auth.get_session_index()
        self_url = OneLogin_Saml2_Utils.get_self_url(req)
        self_url = self_url+req['script_name']
        if 'RelayState' in request.form and self_url != request.form['RelayState']:
            return redirect(auth.redirect_to(request.form['RelayState']))
        user = User.query.filter_by(username=session['samlNameId'].lower()).first()
        if not user:
            # create user
            user = User(username=session['samlNameId'],
                        plain_text_password = None,
                        email=session['samlNameId'])
            user.create_local_user()
        session['user_id'] = user.id
        if session['samlUserdata'].has_key("email"):
            user.email = session['samlUserdata']["email"][0].lower()
        if session['samlUserdata'].has_key("givenname"):
            user.firstname = session['samlUserdata']["givenname"][0]
        if session['samlUserdata'].has_key("surname"):
            user.lastname = session['samlUserdata']["surname"][0]
        user.plain_text_password = None
        user.update_profile()
        session['external_auth'] = True
        login_user(user, remember=False)
        return redirect(url_for('index'))
    else:
        return  render_template('errors/SAML.html', errors=errors)

@app.route('/login', methods=['GET', 'POST'])
@login_manager.unauthorized_handler
def login():
    LOGIN_TITLE = app.config['LOGIN_TITLE'] if 'LOGIN_TITLE' in app.config.keys() else ''
    BASIC_ENABLED = app.config['BASIC_ENABLED']
    SIGNUP_ENABLED = app.config['SIGNUP_ENABLED']
    LDAP_ENABLED = app.config.get('LDAP_ENABLED')
    GITHUB_ENABLE = app.config.get('GITHUB_OAUTH_ENABLE')
    GOOGLE_ENABLE = app.config.get('GOOGLE_OAUTH_ENABLE')
    SAML_ENABLED = app.config.get('SAML_ENABLED')

    if g.user is not None and current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if 'google_token' in session:
        user_data = google.get('userinfo').data
        first_name = user_data['given_name']
        surname = user_data['family_name']
        email = user_data['email']
        user = User.query.filter_by(username=email).first()
        if not user:
            # create user
            user = User(username=email,
                        firstname=first_name,
                        lastname=surname,
                        plain_text_password=None,
                        email=email)

            result = user.create_local_user()
            if not result['status']:
                session.pop('google_token', None)
                return redirect(url_for('login'))

        session['user_id'] = user.id
        login_user(user, remember = False)
        session['external_auth'] = True
        return redirect(url_for('index'))

    if 'github_token' in session:
        me = github.get('user')
        user_info = me.data
        user = User.query.filter_by(username=user_info['name']).first()
        if not user:
            # create user
            user = User(username=user_info['name'],
                        plain_text_password=None,
                        email=user_info['email'])

            result = user.create_local_user()
            if not result['status']:
                session.pop('github_token', None)
                return redirect(url_for('login'))

        session['user_id'] = user.id
        session['external_auth'] = True
        login_user(user, remember = False)
        return redirect(url_for('index'))

    if request.method == 'GET':
        return render_template('login.html', github_enabled=GITHUB_ENABLE,
                                             google_enabled=GOOGLE_ENABLE,
                                             saml_enabled=SAML_ENABLED,
                                             ldap_enabled=LDAP_ENABLED,
                                             login_title=LOGIN_TITLE,
                                             basic_enabled=BASIC_ENABLED,
                                             signup_enabled=SIGNUP_ENABLED)

    # process login
    username = request.form['username']
    password = request.form['password']
    otp_token = request.form.get('otptoken')
    auth_method = request.form.get('auth_method', 'LOCAL')

    # addition fields for registration case
    firstname = request.form.get('firstname')
    lastname = request.form.get('lastname')
    email = request.form.get('email')
    rpassword = request.form.get('rpassword')

    if auth_method != 'LOCAL':
        session['external_auth'] = True

    if None in [firstname, lastname, email]:
        #login case
        remember_me = False
        if 'remember' in request.form:
            remember_me = True

        user = User(username=username, password=password, plain_text_password=password)

        try:
            auth = user.is_validate(method=auth_method, src_ip=request.remote_addr)
            if auth == False:
                return render_template('login.html', error='Invalid credentials',
                                                     github_enabled=GITHUB_ENABLE,
                                                     google_enabled=GOOGLE_ENABLE,
                                                     saml_enabled=SAML_ENABLED,
                                                     ldap_enabled=LDAP_ENABLED,
                                                     login_title=LOGIN_TITLE,
                                                     basic_enabled=BASIC_ENABLED,
                                                     signup_enabled=SIGNUP_ENABLED)
        except Exception as e:
            return render_template('login.html', error=e,
                                                 github_enabled=GITHUB_ENABLE,
                                                 google_enabled=GOOGLE_ENABLE,
                                                 saml_enabled=SAML_ENABLED,
                                                 ldap_enabled=LDAP_ENABLED,
                                                 login_title=LOGIN_TITLE,
                                                 basic_enabled=BASIC_ENABLED,
                                                 signup_enabled=SIGNUP_ENABLED)

        # check if user enabled OPT authentication
        if user.otp_secret:
            if otp_token and otp_token.isdigit():
                good_token = user.verify_totp(otp_token)
                if not good_token:
                    return render_template('login.html', error='Invalid credentials',
                                                         github_enabled=GITHUB_ENABLE,
                                                         google_enabled=GOOGLE_ENABLE,
                                                         saml_enabled=SAML_ENABLED,
                                                         ldap_enabled=LDAP_ENABLED,
                                                         login_title=LOGIN_TITLE,
                                                         basic_enabled=BASIC_ENABLED,
                                                         signup_enabled=SIGNUP_ENABLED)
            else:
                return render_template('login.html', error='Token required',
                                                     github_enabled=GITHUB_ENABLE,
                                                     google_enabled=GOOGLE_ENABLE,
                                                     saml_enabled=SAML_ENABLED,
                                                     ldap_enabled=LDAP_ENABLED,
                                                     login_title=LOGIN_TITLE,
                                                     basic_enabled=BASIC_ENABLED,
                                                     signup_enabled=SIGNUP_ENABLED)

        login_user(user, remember = remember_me)
        return redirect(request.args.get('next') or url_for('index'))
    else:
        if not username or not password or not email:
            return render_template('register.html', error='Please input required information')

        # registration case
        user = User(username=username, plain_text_password=password, firstname=firstname, lastname=lastname, email=email)

        # TODO: Move this into the JavaScript
        # validate password and password confirmation
        if password != rpassword:
            error = "Password confirmation does not match"
            return render_template('register.html', error=error)

        try:
            result = user.create_local_user()
            if result == True:
                return render_template('login.html', username=username, password=password,
                                                     github_enabled=GITHUB_ENABLE,
                                                     google_enabled=GOOGLE_ENABLE,
                                                     saml_enabled=SAML_ENABLED,
                                                     ldap_enabled=LDAP_ENABLED,
                                                     login_title=LOGIN_TITLE,
                                                     basic_enabled=BASIC_ENABLED,
                                                     signup_enabled=SIGNUP_ENABLED)
            else:
                return render_template('register.html', error=result['msg'])
        except Exception as e:
            return render_template('register.html', error=e)

def clear_session():
    session.pop('user_id', None)
    session.pop('github_token', None)
    session.pop('google_token', None)
    session.clear()
    logout_user()

@app.route('/logout')
def logout():
    if app.config.get('SAML_ENABLED') and 'samlSessionIndex' in session and app.config.get('SAML_LOGOUT'):
        req = utils.prepare_flask_request(request)
        auth = utils.init_saml_auth(req)
        if app.config.get('SAML_LOGOUT_URL'):
            return redirect(auth.logout(name_id_format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                                        return_to = app.config.get('SAML_LOGOUT_URL'),
                            session_index = session['samlSessionIndex'], name_id=session['samlNameId']))
        return redirect(auth.logout(name_id_format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                        session_index = session['samlSessionIndex'],
                                    name_id=session['samlNameId']))
    clear_session()
    return redirect(url_for('login'))

@app.route('/saml/sls')
def saml_logout():
    req = utils.prepare_flask_request(request)
    auth = utils.init_saml_auth(req)
    url = auth.process_slo()
    errors = auth.get_errors()
    if len(errors) == 0:
        clear_session()
        if url is not None:
            return redirect(url)
        elif app.config.get('SAML_LOGOUT_URL') is not None:
            return redirect(app.config.get('SAML_LOGOUT_URL'))
        else:
            return redirect(url_for('login'))
    else:
        return render_template('errors/SAML.html', errors=errors)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if not app.config.get('BG_DOMAIN_UPDATES'):
        logging.debug('Update domains in foreground')
        d = Domain().update()
    else:
        logging.debug('Update domains in background')

    # stats for dashboard
    domain_count = Domain.query.count()
    users = User.query.all()
    history_number = History.query.count()
    history = History.query.order_by(History.created_on.desc()).limit(4)
    server = Server(server_id='localhost')
    statistics = server.get_statistic()
    if statistics:
        uptime = list([uptime for uptime in statistics if uptime['name'] == 'uptime'])[0]['value']
    else:
        uptime = 0

    return render_template('dashboard.html', domain_count=domain_count, users=users, history_number=history_number, uptime=uptime, histories=history, dnssec_adm_only=app.config['DNSSEC_ADMINS_ONLY'], pdns_version=app.config['PDNS_VERSION'], show_bg_domain_button=app.config['BG_DOMAIN_UPDATES'])


@app.route('/dashboard-domains', methods=['GET'])
@login_required
def dashboard_domains():
    if current_user.role.name == 'Administrator':
        domains = Domain.query
    else:
        domains = User(id=current_user.id).get_domain_query()

    template = app.jinja_env.get_template("dashboard_domain.html")
    render = template.make_module(vars={"current_user": current_user})

    columns = [Domain.name, Domain.dnssec, Domain.type, Domain.serial, Domain.master, Domain.account]
    # History.created_on.desc()
    order_by = []
    for i in range(len(columns)):
        column_index = request.args.get("order[{0}][column]".format(i))
        sort_direction = request.args.get("order[{0}][dir]".format(i))
        if column_index is None:
            break
        if sort_direction != "asc" and sort_direction != "desc":
            sort_direction = "asc"

        column = columns[int(column_index)]
        order_by.append(getattr(column, sort_direction)())

    if order_by:
        domains = domains.order_by(*order_by)

    total_count = domains.count()

    search = request.args.get("search[value]")
    if search:
        start = "" if search.startswith("^") else "%"
        end = "" if search.endswith("$") else "%"

        if current_user.role.name == 'Administrator':
            domains = domains.outerjoin(Account).filter(Domain.name.ilike(start + search.strip("^$") + end) |
                                                        Account.name.ilike(start + search.strip("^$") + end) |
                                                        Account.description.ilike(start + search.strip("^$") + end))
        else:
            domains = domains.filter(Domain.name.ilike(start + search.strip("^$") + end))

    filtered_count = domains.count()

    start = int(request.args.get("start", 0))
    length = min(int(request.args.get("length", 0)), 100)

    if length != -1:
        domains = domains[start:start + length]

    data = []
    for domain in domains:
        data.append([
            render.name(domain),
            render.dnssec(domain),
            render.type(domain),
            render.serial(domain),
            render.master(domain),
            render.account(domain),
            render.actions(domain),
        ])

    response_data = {
        "draw": int(request.args.get("draw", 0)),
        "recordsTotal": total_count,
        "recordsFiltered": filtered_count,
        "data": data,
    }
    return jsonify(response_data)

@app.route('/dashboard-domains-updater', methods=['GET', 'POST'])
@login_required
def dashboard_domains_updater():
    logging.debug('Update domains in background')
    d = Domain().update()

    response_data = {
        "result": d,
    }
    return jsonify(response_data)


@app.route('/domain/<path:domain_name>', methods=['GET', 'POST'])
@login_required
@can_access_domain
def domain(domain_name):
    r = Record()
    domain = Domain.query.filter(Domain.name == domain_name).first()
    if not domain:
        return redirect(url_for('error', code=404))

    # query domain info from PowerDNS API
    zone_info = r.get_record_data(domain.name)
    if zone_info:
        jrecords = zone_info['records']
    else:
        # can not get any record, API server might be down
        return redirect(url_for('error', code=500))

    quick_edit = strtobool(Setting().get('allow_quick_edit'))

    records = []
    #TODO: This should be done in the "model" instead of "view"
    if NEW_SCHEMA:
        for jr in jrecords:
            if jr['type'] in app.config['RECORDS_ALLOW_EDIT']:
                for subrecord in jr['records']:
                    record = Record(name=jr['name'], type=jr['type'], status='Disabled' if subrecord['disabled'] else 'Active', ttl=jr['ttl'], data=subrecord['content'])
                    records.append(record)
        if not re.search('ip6\.arpa|in-addr\.arpa$', domain_name):
            editable_records = app.config['RECORDS_ALLOW_EDIT']
        else:
            editable_records = app.config['REVERSE_RECORDS_ALLOW_EDIT']
        return render_template('domain.html', domain=domain, records=records, editable_records=editable_records, quick_edit=quick_edit)
    else:
        for jr in jrecords:
            if jr['type'] in app.config['RECORDS_ALLOW_EDIT']:
                record = Record(name=jr['name'], type=jr['type'], status='Disabled' if jr['disabled'] else 'Active', ttl=jr['ttl'], data=jr['content'])
                records.append(record)
    if not re.search('ip6\.arpa|in-addr\.arpa$', domain_name):
        editable_records = app.config['FORWARD_RECORDS_ALLOW_EDIT']
    else:
        editable_records = app.config['REVERSE_RECORDS_ALLOW_EDIT']
    return render_template('domain.html', domain=domain, records=records, editable_records=editable_records, quick_edit=quick_edit, pdns_version=app.config['PDNS_VERSION'])


@app.route('/admin/domain/add', methods=['GET', 'POST'])
@login_required
@admin_role_required
def domain_add():
    templates = DomainTemplate.query.all()
    if request.method == 'POST':
        try:
            domain_name = request.form.getlist('domain_name')[0]
            domain_type = request.form.getlist('radio_type')[0]
            domain_template = request.form.getlist('domain_template')[0]
            soa_edit_api = request.form.getlist('radio_type_soa_edit_api')[0]
            account_id = request.form.getlist('accountid')[0]

            if ' ' in domain_name or not domain_name or not domain_type:
                return render_template('errors/400.html', msg="Please correct your input"), 400

            if domain_type == 'slave':
                if request.form.getlist('domain_master_address'):
                    domain_master_string = request.form.getlist('domain_master_address')[0]
                    domain_master_string = domain_master_string.replace(' ','')
                    domain_master_ips = domain_master_string.split(',')
            else:
                domain_master_ips = []

            account_name = Account().get_name_by_id(account_id)

            d = Domain()
            result = d.add(domain_name=domain_name, domain_type=domain_type, soa_edit_api=soa_edit_api, domain_master_ips=domain_master_ips, account_name=account_name)
            if result['status'] == 'ok':
                history = History(msg='Add domain {0}'.format(domain_name), detail=str({'domain_type': domain_type, 'domain_master_ips': domain_master_ips, 'account_id': account_id}), created_by=current_user.username)
                history.add()
                if domain_template != '0':
                    template = DomainTemplate.query.filter(DomainTemplate.id == domain_template).first()
                    template_records = DomainTemplateRecord.query.filter(DomainTemplateRecord.template_id == domain_template).all()
                    record_data = []
                    for template_record in template_records:
                        record_row = {'record_data': template_record.data, 'record_name': template_record.name, 'record_status': template_record.status, 'record_ttl': template_record.ttl, 'record_type': template_record.type}
                        record_data.append(record_row)
                    r = Record()
                    result = r.apply(domain_name, record_data)
                    if result['status'] == 'ok':
                        history = History(msg='Applying template {0} to {1}, created records successfully.'.format(template.name, domain_name), detail=str(result), created_by=current_user.username)
                        history.add()
                    else:
                        history = History(msg='Applying template {0} to {1}, FAILED to created records.'.format(template.name, domain_name), detail=str(result), created_by=current_user.username)
                        history.add()
                return redirect(url_for('dashboard'))
            else:
                return render_template('errors/400.html', msg=result['msg']), 400
        except:
            logging.error(traceback.print_exc())
            return redirect(url_for('error', code=500))

    else:
        accounts = Account.query.all()
        return render_template('domain_add.html', templates=templates, accounts=accounts)


@app.route('/admin/domain/<path:domain_name>/delete', methods=['GET'])
@login_required
@admin_role_required
def domain_delete(domain_name):
    d = Domain()
    result = d.delete(domain_name)

    if result['status'] == 'error':
        return redirect(url_for('error', code=500))

    history = History(msg='Delete domain {0}'.format(domain_name), created_by=current_user.username)
    history.add()

    return redirect(url_for('dashboard'))


@app.route('/admin/domain/<path:domain_name>/manage', methods=['GET', 'POST'])
@login_required
@admin_role_required
def domain_management(domain_name):
    if request.method == 'GET':
        domain = Domain.query.filter(Domain.name == domain_name).first()
        if not domain:
            return redirect(url_for('error', code=404))
        users = User.query.all()
        accounts = Account.query.all()

        # get list of user ids to initilize selection data
        d = Domain(name=domain_name)
        domain_user_ids = d.get_user()
        account = d.get_account()

        return render_template('domain_management.html', domain=domain, users=users, domain_user_ids=domain_user_ids, accounts=accounts, domain_account=account)

    if request.method == 'POST':
        # username in right column
        new_user_list = request.form.getlist('domain_multi_user[]')

        # get list of user ids to compare
        d = Domain(name=domain_name)
        domain_user_ids = d.get_user()

        # grant/revoke user privielges
        d.grant_privielges(new_user_list)

        history = History(msg='Change domain {0} access control'.format(domain_name), detail=str({'user_has_access': new_user_list}), created_by=current_user.username)
        history.add()

        return redirect(url_for('domain_management', domain_name=domain_name))


@app.route('/admin/domain/<path:domain_name>/change_soa_setting', methods=['POST'])
@login_required
@admin_role_required
def domain_change_soa_edit_api(domain_name):
    domain = Domain.query.filter(Domain.name == domain_name).first()
    if not domain:
        return redirect(url_for('error', code=404))
    new_setting = request.form.get('soa_edit_api')
    if new_setting == None:
        return redirect(url_for('error', code=500))
    if new_setting == '0':
        return redirect(url_for('domain_management', domain_name=domain_name))

    d = Domain()
    status = d.update_soa_setting(domain_name=domain_name, soa_edit_api=new_setting)
    if status['status'] != None:
        users = User.query.all()
        accounts = Account.query.all()
        d = Domain(name=domain_name)
        domain_user_ids = d.get_user()
        account = d.get_account()
        return render_template('domain_management.html', domain=domain, users=users, domain_user_ids=domain_user_ids, accounts=accounts, domain_account=account)
    else:
        return redirect(url_for('error', code=500))


@app.route('/admin/domain/<path:domain_name>/change_account', methods=['POST'])
@login_required
@admin_role_required
def domain_change_account(domain_name):
    domain = Domain.query.filter(Domain.name == domain_name).first()
    if not domain:
        return redirect(url_for('error', code=404))

    account_id = request.form.get('accountid')
    status = domain.assoc_account(account_id)
    if status['status']:
        users = User.query.all()
        accounts = Account.query.all()
        d = Domain(name=domain_name)
        domain_user_ids = d.get_user()
        account = d.get_account()
        return render_template('domain_management.html', domain=domain, users=users, domain_user_ids=domain_user_ids, accounts=accounts, domain_account=account)
    else:
        return redirect(url_for('error', code=500))


@app.route('/domain/<path:domain_name>/apply', methods=['POST'], strict_slashes=False)
@login_required
@can_access_domain
def record_apply(domain_name):
    """
    example jdata: {u'record_ttl': u'1800', u'record_type': u'CNAME', u'record_name': u'test4', u'record_status': u'Active', u'record_data': u'duykhanh.me'}
    """
    #TODO: filter removed records / name modified records.

    try:
        jdata = request.json

        submitted_serial = jdata['serial']
        submitted_record = jdata['record']

        domain = Domain.query.filter(Domain.name==domain_name).first()

        logging.debug('Your submitted serial: {0}'.format(submitted_serial))
        logging.debug('Current domain serial: {0}'.format(domain.serial))

        if domain:
            if int(submitted_serial) != domain.serial:
                return make_response(jsonify( {'status': 'error', 'msg': 'The zone has been changed by another session or user. Please refresh this web page to load updated records.'} ), 500)
        else:
            return make_response(jsonify( {'status': 'error', 'msg': 'Domain name {0} does not exist'.format(domain_name)} ), 404)

        r = Record()
        result = r.apply(domain_name, submitted_record)
        if result['status'] == 'ok':
            history = History(msg='Apply record changes to domain {0}'.format(domain_name), detail=str(jdata), created_by=current_user.username)
            history.add()
            return make_response(jsonify( result ), 200)
        else:
            return make_response(jsonify( result ), 400)
    except:
        logging.error(traceback.print_exc())
        return make_response(jsonify( {'status': 'error', 'msg': 'Error when applying new changes'} ), 500)


@app.route('/domain/<path:domain_name>/update', methods=['POST'], strict_slashes=False)
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
            return make_response(jsonify( {'status': 'ok', 'msg': result['msg']} ), 200)
        else:
            return make_response(jsonify( {'status': 'error', 'msg': result['msg']} ), 500)
    except:
        logging.error(traceback.print_exc())
        return make_response(jsonify( {'status': 'error', 'msg': 'Error when applying new changes'} ), 500)


@app.route('/domain/<path:domain_name>/record/<path:record_name>/type/<path:record_type>/delete', methods=['GET'])
@login_required
@admin_role_required
def record_delete(domain_name, record_name, record_type):
    try:
        r = Record(name=record_name, type=record_type)
        result = r.delete(domain=domain_name)
        if result['status'] == 'error':
            print(result['msg'])
    except:
        logging.error(traceback.print_exc())
        return redirect(url_for('error', code=500)), 500
    return redirect(url_for('domain', domain_name=domain_name))


@app.route('/domain/<path:domain_name>/info', methods=['GET'])
@login_required
@can_access_domain
def domain_info(domain_name):
    domain = Domain()
    domain_info = domain.get_domain_info(domain_name)
    return make_response(jsonify(domain_info), 200)


@app.route('/domain/<path:domain_name>/dnssec', methods=['GET'])
@login_required
@can_access_domain
def domain_dnssec(domain_name):
    domain = Domain()
    dnssec = domain.get_domain_dnssec(domain_name)
    return make_response(jsonify(dnssec), 200)


@app.route('/domain/<path:domain_name>/dnssec/enable', methods=['GET'])
@login_required
@can_access_domain
@can_configure_dnssec
def domain_dnssec_enable(domain_name):
    domain = Domain()
    dnssec = domain.enable_domain_dnssec(domain_name)
    return make_response(jsonify(dnssec), 200)


@app.route('/domain/<path:domain_name>/dnssec/disable', methods=['GET'])
@login_required
@can_access_domain
@can_configure_dnssec
def domain_dnssec_disable(domain_name):
    domain = Domain()
    dnssec = domain.get_domain_dnssec(domain_name)

    for key in dnssec['dnssec']:
        response = domain.delete_dnssec_key(domain_name,key['id']);

    return make_response(jsonify( { 'status': 'ok', 'msg': 'DNSSEC removed.' } ))


@app.route('/domain/<path:domain_name>/managesetting', methods=['GET', 'POST'])
@login_required
@admin_role_required
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
                domain = Domain.query.filter(Domain.name == domain_name).first()
                setting = DomainSetting.query.filter(DomainSetting.domain == domain).filter(DomainSetting.setting == new_setting).first()

                if setting:
                    if setting.set(new_value):
                        history = History(msg='Setting {0} changed value to {1} for {2}'.format(new_setting, new_value, domain.name), created_by=current_user.username)
                        history.add()
                        return make_response(jsonify( { 'status': 'ok', 'msg': 'Setting updated.' } ))
                    else:
                        return make_response(jsonify( { 'status': 'error', 'msg': 'Unable to set value of setting.' } ))
                else:
                    if domain.add_setting(new_setting, new_value):
                        history = History(msg='New setting {0} with value {1} for {2} has been created'.format(new_setting, new_value, domain.name), created_by=current_user.username)
                        history.add()
                        return make_response(jsonify( { 'status': 'ok', 'msg': 'New setting created and updated.' } ))
                    else:
                        return make_response(jsonify( { 'status': 'error', 'msg': 'Unable to create new setting.' } ))
            else:
                return make_response(jsonify( { 'status': 'error', 'msg': 'Action not supported.' } ), 400)
        except:
            logging.error(traceback.print_exc())
            return make_response(jsonify( { 'status': 'error', 'msg': 'There is something wrong, please contact Administrator.' } ), 400)


@app.route('/templates', methods=['GET', 'POST'])
@app.route('/templates/list', methods=['GET', 'POST'])
@login_required
@admin_role_required
def templates():
    templates = DomainTemplate.query.all()
    return render_template('template.html', templates=templates)


@app.route('/template/create', methods=['GET', 'POST'])
@login_required
@admin_role_required
def create_template():
    if request.method == 'GET':
        return render_template('template_add.html')
    if request.method == 'POST':
        try:
            name = request.form.getlist('name')[0]
            description = request.form.getlist('description')[0]

            if ' ' in name or not name or not type:
                flash("Please correct your input", 'error')
                return redirect(url_for('create_template'))

            if DomainTemplate.query.filter(DomainTemplate.name == name).first():
                flash("A template with the name {0} already exists!".format(name), 'error')
                return redirect(url_for('create_template'))
            t = DomainTemplate(name=name, description=description)
            result = t.create()
            if result['status'] == 'ok':
                history = History(msg='Add domain template {0}'.format(name), detail=str({'name': name, 'description': description}), created_by=current_user.username)
                history.add()
                return redirect(url_for('templates'))
            else:
                flash(result['msg'], 'error')
                return redirect(url_for('create_template'))
        except:
            logging.error(traceback.print_exc())
            return redirect(url_for('error', code=500))
        return redirect(url_for('templates'))


@app.route('/template/createfromzone', methods=['POST'])
@login_required
@admin_role_required
def create_template_from_zone():
    try:
        jdata = request.json
        name = jdata['name']
        description = jdata['description']
        domain_name = jdata['domain']

        if ' ' in name or not name or not type:
            return make_response(jsonify({'status': 'error', 'msg': 'Please correct template name'}), 500)

        if DomainTemplate.query.filter(DomainTemplate.name == name).first():
            return make_response(jsonify({'status': 'error', 'msg': 'A template with the name {0} already exists!'.format(name)}), 500)

        t = DomainTemplate(name=name, description=description)
        result = t.create()
        if result['status'] == 'ok':
            history = History(msg='Add domain template {0}'.format(name), detail=str({'name': name, 'description': description}), created_by=current_user.username)
            history.add()

            records = []
            r = Record()
            domain = Domain.query.filter(Domain.name == domain_name).first()
            if domain:
                # query domain info from PowerDNS API
                zone_info = r.get_record_data(domain.name)
                if zone_info:
                    jrecords = zone_info['records']

                if NEW_SCHEMA:
                    for jr in jrecords:
                        if jr['type'] in app.config['RECORDS_ALLOW_EDIT']:
                            name = '@' if jr['name'] == domain_name else re.sub('\.{}$'.format(domain_name), '', jr['name'])
                            for subrecord in jr['records']:
                                record = DomainTemplateRecord(name=name, type=jr['type'], status=True if subrecord['disabled'] else False, ttl=jr['ttl'], data=subrecord['content'])
                                records.append(record)
                else:
                    for jr in jrecords:
                        if jr['type'] in app.config['RECORDS_ALLOW_EDIT']:
                            name = '@' if jr['name'] == domain_name else re.sub('\.{}$'.format(domain_name), '', jr['name'])
                            record = DomainTemplateRecord(name=name, type=jr['type'], status=True if jr['disabled'] else False, ttl=jr['ttl'], data=jr['content'])
                            records.append(record)

            result_records = t.replace_records(records)

            if result_records['status'] == 'ok':
                    return make_response(jsonify({'status': 'ok', 'msg': result['msg']}), 200)
            else:
                result = t.delete_template()
                return make_response(jsonify({'status': 'error', 'msg': result_records['msg']}), 500)

        else:
            return make_response(jsonify({'status': 'error', 'msg': result['msg']}), 500)
    except:
        logging.error(traceback.print_exc())
        return make_response(jsonify({'status': 'error', 'msg': 'Error when applying new changes'}), 500)


@app.route('/template/<path:template>/edit', methods=['GET'])
@login_required
@admin_role_required
def edit_template(template):
    try:
        t = DomainTemplate.query.filter(DomainTemplate.name == template).first()
        if t is not None:
            records = []
            for jr in t.records:
                if jr.type in app.config['RECORDS_ALLOW_EDIT']:
                        record = DomainTemplateRecord(name=jr.name, type=jr.type, status='Disabled' if jr.status else 'Active', ttl=jr.ttl, data=jr.data)
                        records.append(record)

            return render_template('template_edit.html', template=t.name, records=records, editable_records=app.config['RECORDS_ALLOW_EDIT'])
    except:
        logging.error(traceback.print_exc())
        return redirect(url_for('error', code=500))
    return redirect(url_for('templates'))


@app.route('/template/<path:template>/apply', methods=['POST'], strict_slashes=False)
@login_required
def apply_records(template):
    try:
        jdata = request.json
        records = []

        for j in jdata:
            name = '@' if j['record_name'] in ['@', ''] else j['record_name']
            type = j['record_type']
            data = j['record_data']
            disabled = True if j['record_status'] == 'Disabled' else False
            ttl = int(j['record_ttl']) if j['record_ttl'] else 3600

            dtr = DomainTemplateRecord(name=name, type=type, data=data, status=disabled, ttl=ttl)
            records.append(dtr)

        t = DomainTemplate.query.filter(DomainTemplate.name == template).first()
        result = t.replace_records(records)
        if result['status'] == 'ok':
            history = History(msg='Apply domain template record changes to domain template {0}'.format(template), detail=str(jdata), created_by=current_user.username)
            history.add()
            return make_response(jsonify(result), 200)
        else:
            return make_response(jsonify(result), 400)
    except:
        logging.error(traceback.print_exc())
        return make_response(jsonify({'status': 'error', 'msg': 'Error when applying new changes'}), 500)


@app.route('/template/<path:template>/delete', methods=['GET'])
@login_required
@admin_role_required
def delete_template(template):
    try:
        t = DomainTemplate.query.filter(DomainTemplate.name == template).first()
        if t is not None:
            result = t.delete_template()
            if result['status'] == 'ok':
                history = History(msg='Deleted domain template {0}'.format(template), detail=str({'name': template}), created_by=current_user.username)
                history.add()
                return redirect(url_for('templates'))
            else:
                flash(result['msg'], 'error')
                return redirect(url_for('templates'))
    except:
        logging.error(traceback.print_exc())
        return redirect(url_for('error', code=500))
    return redirect(url_for('templates'))


@app.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_role_required
def admin():
    domains = Domain.query.all()
    users = User.query.all()

    server = Server(server_id='localhost')
    configs = server.get_config()
    statistics = server.get_statistic()
    history_number = History.query.count()

    if statistics:
        uptime = list([uptime for uptime in statistics if uptime['name'] == 'uptime'])[0]['value']
    else:
        uptime = 0

    return render_template('admin.html', domains=domains, users=users, configs=configs, statistics=statistics, uptime=uptime, history_number=history_number)


@app.route('/admin/user/create', methods=['GET', 'POST'])
@login_required
@admin_role_required
def admin_createuser():
    if request.method == 'GET':
        return render_template('admin_createuser.html')

    if request.method == 'POST':
        fdata = request.form

        user = User(username=fdata['username'], plain_text_password=fdata['password'], firstname=fdata['firstname'], lastname=fdata['lastname'], email=fdata['email'])

        if fdata['password'] == "":
            return render_template('admin_createuser.html', user=user, blank_password=True)

        result = user.create_local_user();
        if result['status']:
            return redirect(url_for('admin_manageuser'))

        return render_template('admin_createuser.html', user=user, error=result['msg'])


@app.route('/admin/manageuser', methods=['GET', 'POST'])
@login_required
@admin_role_required
def admin_manageuser():
    if request.method == 'GET':
        users = User.query.order_by(User.username).all()
        return render_template('admin_manageuser.html', users=users)

    if request.method == 'POST':
        #
        # post data should in format
        # {'action': 'delete_user', 'data': 'username'}
        #
        try:
            jdata = request.json
            data = jdata['data']

            if jdata['action'] == 'delete_user':
                user = User(username=data)
                if user.username == current_user.username:
                    return make_response(jsonify( { 'status': 'error', 'msg': 'You cannot delete yourself.' } ), 400)
                result = user.delete()
                if result:
                    history = History(msg='Delete username {0}'.format(data), created_by=current_user.username)
                    history.add()
                    return make_response(jsonify( { 'status': 'ok', 'msg': 'User has been removed.' } ), 200)
                else:
                    return make_response(jsonify( { 'status': 'error', 'msg': 'Cannot remove user.' } ), 500)

            elif jdata['action'] == 'revoke_user_privielges':
                user = User(username=data)
                result = user.revoke_privilege()
                if result:
                    history = History(msg='Revoke {0} user privielges'.format(data), created_by=current_user.username)
                    history.add()
                    return make_response(jsonify( { 'status': 'ok', 'msg': 'Revoked user privielges.' } ), 200)
                else:
                    return make_response(jsonify( { 'status': 'error', 'msg': 'Cannot revoke user privilege.' } ), 500)

            elif jdata['action'] == 'set_admin':
                username = data['username']
                if username == current_user.username:
                    return make_response(jsonify( { 'status': 'error', 'msg': 'You cannot change you own admin rights.' } ), 400)
                is_admin = data['is_admin']
                user = User(username=username)
                result = user.set_admin(is_admin)
                if result:
                    history = History(msg='Change user role of {0}'.format(username), created_by=current_user.username)
                    history.add()
                    return make_response(jsonify( { 'status': 'ok', 'msg': 'Changed user role successfully.' } ), 200)
                else:
                    return make_response(jsonify( { 'status': 'error', 'msg': 'Cannot change user role.' } ), 500)
            else:
                return make_response(jsonify( { 'status': 'error', 'msg': 'Action not supported.' } ), 400)
        except:
            logging.error(traceback.print_exc())
            return make_response(jsonify( { 'status': 'error', 'msg': 'There is something wrong, please contact Administrator.' } ), 400)


@app.route('/admin/account/edit/<account_name>', methods=['GET', 'POST'])
@app.route('/admin/account/edit', methods=['GET', 'POST'])
@login_required
@admin_role_required
def admin_editaccount(account_name=None):
    users = User.query.all()

    if request.method == 'GET':
        if account_name is None:
            return render_template('admin_editaccount.html', users=users, create=1)

        else:
            account = Account.query.filter(Account.name == account_name).first()
            account_user_ids = account.get_user()
            return render_template('admin_editaccount.html', account=account, account_user_ids=account_user_ids, users=users, create=0)

    if request.method == 'POST':
        fdata = request.form
        new_user_list = request.form.getlist('account_multi_user')

        # on POST, synthesize account and account_user_ids from form data
        if not account_name:
            account_name = fdata['accountname']

        account = Account(name=account_name, description=fdata['accountdescription'], contact=fdata['accountcontact'], mail=fdata['accountmail'])
        account_user_ids = []
        for username in new_user_list:
            userid = User(username=username).get_user_info_by_username().id
            account_user_ids.append(userid)

        create = int(fdata['create'])
        if create:
            # account __init__ sanitizes and lowercases the name, so to manage expectations
            # we let the user reenter the name until it's not empty and it's valid (ignoring the case)
            if account.name == "" or account.name != account_name.lower():
                return render_template('admin_editaccount.html', account=account, account_user_ids=account_user_ids, users=users, create=create, invalid_accountname=True)

            if Account.query.filter(Account.name == account.name).first():
                return render_template('admin_editaccount.html', account=account, account_user_ids=account_user_ids, users=users, create=create, duplicate_accountname=True)

            result = account.create_account()
            history = History(msg='Create account {0}'.format(account.name), created_by=current_user.username)

        else:
            result = account.update_account()
            history = History(msg='Update account {0}'.format(account.name), created_by=current_user.username)

        if result['status']:
            account.grant_privileges(new_user_list)
            history.add()
            return redirect(url_for('admin_manageaccount'))

        return render_template('admin_editaccount.html', account=account, account_user_ids=account_user_ids, users=users, create=create, error=result['msg'])


@app.route('/admin/manageaccount', methods=['GET', 'POST'])
@login_required
@admin_role_required
def admin_manageaccount():
    if request.method == 'GET':
        accounts = Account.query.order_by(Account.name).all()
        return render_template('admin_manageaccount.html', accounts=accounts)

    if request.method == 'POST':
        #
        # post data should in format
        # {'action': 'delete_account', 'data': 'accountname'}
        #
        try:
            jdata = request.json
            data = jdata['data']

            if jdata['action'] == 'delete_account':
                account = Account(name=data)
                result = account.delete_account()
                if result:
                    history = History(msg='Delete account {0}'.format(data), created_by=current_user.username)
                    history.add()
                    return make_response(jsonify( { 'status': 'ok', 'msg': 'Account has been removed.' } ), 200)
                else:
                    return make_response(jsonify( { 'status': 'error', 'msg': 'Cannot remove account.' } ), 500)

            else:
                return make_response(jsonify( { 'status': 'error', 'msg': 'Action not supported.' } ), 400)
        except:
            logging.error(traceback.print_exc())
            return make_response(jsonify( { 'status': 'error', 'msg': 'There is something wrong, please contact Administrator.' } ), 400)


@app.route('/admin/history', methods=['GET', 'POST'])
@login_required
@admin_role_required
def admin_history():
    if request.method == 'POST':
        h = History()
        result = h.remove_all()
        if result:
            history = History(msg='Remove all histories', created_by=current_user.username)
            history.add()

            return make_response(jsonify( { 'status': 'ok', 'msg': 'Changed user role successfully.' } ), 200)
        else:
            return make_response(jsonify( { 'status': 'error', 'msg': 'Can not remove histories.' } ), 500)

    if request.method == 'GET':
        histories = History.query.all()
        return render_template('admin_history.html', histories=histories)


@app.route('/admin/settings', methods=['GET'])
@login_required
@admin_role_required
def admin_settings():
    if request.method == 'GET':
        # start with a copy of the setting defaults (ignore maintenance setting)
        settings = Setting.defaults.copy()
        settings.pop('maintenance', None)

        # update settings info with any customizations
        for s in settings:
            value = Setting().get(s)
            if value is not None:
                settings[s] = value

        return render_template('admin_settings.html', settings=settings)


@app.route('/admin/setting/<path:setting>/toggle', methods=['POST'])
@login_required
@admin_role_required
def admin_settings_toggle(setting):
    result = Setting().toggle(setting)
    if (result):
        return make_response(jsonify( { 'status': 'ok', 'msg': 'Toggled setting successfully.' } ), 200)
    else:
        return make_response(jsonify( { 'status': 'error', 'msg': 'Unable to toggle setting.' } ), 500)


@app.route('/admin/setting/<path:setting>/edit', methods=['POST'])
@login_required
@admin_role_required
def admin_settings_edit(setting):
    jdata = request.json
    new_value = jdata['value']
    result = Setting().set(setting, new_value)

    if (result):
        return make_response(jsonify( { 'status': 'ok', 'msg': 'Toggled setting successfully.' } ), 200)
    else:
        return make_response(jsonify( { 'status': 'error', 'msg': 'Unable to toggle setting.' } ), 500)


@app.route('/user/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    external_account = False
    if 'external_auth' in session:
        external_account = session['external_auth']
    if request.method == 'GET' or external_account:
        return render_template('user_profile.html', external_account=external_account)
    if request.method == 'POST':
        # get new profile info
        firstname = request.form['firstname'] if 'firstname' in request.form else ''
        lastname = request.form['lastname'] if 'lastname' in request.form else ''
        email = request.form['email'] if 'email' in request.form else ''
        new_password = request.form['password'] if 'password' in request.form else ''

        # json data
        if request.data:
            jdata = request.json
            data = jdata['data']
            if jdata['action'] == 'enable_otp':
                enable_otp = data['enable_otp']
                user = User(username=current_user.username)
                user.update_profile(enable_otp=enable_otp)
                return make_response(jsonify( { 'status': 'ok', 'msg': 'Change OTP Authentication successfully. Status: {0}'.format(enable_otp) } ), 200)

        # get new avatar
        save_file_name = None
        if 'file' in request.files:
            file = request.files['file']
            if file:
                filename = secure_filename(file.filename)
                file_extension = filename.rsplit('.', 1)[1]

                if file_extension.lower() in ['jpg', 'jpeg', 'png']:
                    save_file_name = current_user.username + '.' + file_extension
                    file.save(os.path.join(app.config['UPLOAD_DIR'], 'avatar', save_file_name))

        # update user profile
        user = User(username=current_user.username, plain_text_password=new_password, firstname=firstname, lastname=lastname, email=email, avatar=save_file_name, reload_info=False)
        user.update_profile()

        return render_template('user_profile.html', external_account=external_account)


@app.route('/user/avatar/<path:filename>')
def user_avatar(filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_DIR'], 'avatar'), filename)


@app.route('/qrcode')
@login_required
def qrcode():
    if not current_user:
        return redirect(url_for('index'))

    # render qrcode for FreeTOTP
    img = qrc.make(current_user.get_totp_uri(), image_factory=qrc_svg.SvgImage)
    stream = BytesIO()
    img.save(stream)
    return stream.getvalue(), 200, {
        'Content-Type': 'image/svg+xml',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'}


@app.route('/nic/checkip.html', methods=['GET', 'POST'])
def dyndns_checkip():
    # route covers the default ddclient 'web' setting for the checkip service
    return render_template('dyndns.html', response=request.environ.get('HTTP_X_REAL_IP', request.remote_addr))


@app.route('/nic/update', methods=['GET', 'POST'])
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

    try:
        # get all domains owned by the current user
        domains = User(id=current_user.id).get_domain()
    except:
        return render_template('dyndns.html', response='911'), 200

    domain = None
    domain_segments = hostname.split('.')
    for index in range(len(domain_segments)):
        full_domain = '.'.join(domain_segments)
        potential_domain = Domain.query.filter(Domain.name == full_domain).first()
        if potential_domain in domains:
            domain = potential_domain
            break
        domain_segments.pop(0)

    if not domain:
        history = History(msg="DynDNS update: attempted update of {0} but it does not exist for this user".format(hostname), created_by=current_user.username)
        history.add()
        return render_template('dyndns.html', response='nohost'), 200

    r = Record()
    r.name = hostname
    # check if the user requested record exists within this domain
    if r.exists(domain.name) and r.is_allowed_edit():
        if r.data == myip:
            # record content did not change, return 'nochg'
            history = History(msg="DynDNS update: attempted update of {0} but record did not change".format(hostname), created_by=current_user.username)
            history.add()
            return render_template('dyndns.html', response='nochg'), 200
        else:
            oldip = r.data
            result = r.update(domain.name, myip)
            if result['status'] == 'ok':
                history = History(msg='DynDNS update: updated record {0} in zone {1}, it changed from {2} to {3}'.format(hostname,domain.name,oldip,myip), detail=str(result), created_by=current_user.username)
                history.add()
                return render_template('dyndns.html', response='good'), 200
            else:
                return render_template('dyndns.html', response='911'), 200
    elif r.is_allowed_edit():
        ondemand_creation = DomainSetting.query.filter(DomainSetting.domain == domain).filter(DomainSetting.setting == 'create_via_dyndns').first()
        if (ondemand_creation != None) and (strtobool(ondemand_creation.value) == True):
            record = Record(name=hostname,type='A',data=myip,status=False,ttl=3600)
            result = record.add(domain.name)
            if result['status'] == 'ok':
                history = History(msg='DynDNS update: created record {0} in zone {1}, it now represents {2}'.format(hostname,domain.name,myip), detail=str(result), created_by=current_user.username)
                history.add()
                return render_template('dyndns.html', response='good'), 200

    history = History(msg='DynDNS update: attempted update of {0} but it does not exist for this user'.format(hostname), created_by=current_user.username)
    history.add()
    return render_template('dyndns.html', response='nohost'), 200


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    return redirect(url_for('dashboard'))

# END VIEWS
