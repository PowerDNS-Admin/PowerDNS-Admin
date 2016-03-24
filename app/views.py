import os
import json
import jinja2
import traceback

from functools import wraps
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask import Flask, g, request, make_response, jsonify, render_template, session, redirect, url_for, send_from_directory
from werkzeug import secure_filename

from lib import utils
from app import app, login_manager
from .models import User, Role, Domain, DomainUser, Record, Server, History, Anonymous, Setting

jinja2.filters.FILTERS['display_record_name'] = utils.display_record_name
jinja2.filters.FILTERS['display_master_name'] = utils.display_master_name
jinja2.filters.FILTERS['display_second_to_time'] = utils.display_time

# START USER AUTHENTICATION HANDLER
@app.before_request
def before_request():
    # check site maintenance mode first
    maintenance = Setting.query.filter(Setting.name == 'maintenance').first()
    if maintenance and maintenance.value == 'True':
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

# END USER AUTHENTICATION HANDLER

# START CUSTOMIZE DECORATOR
def admin_role_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.role.name != 'Administrator':
            return redirect(url_for('error', code=401))
        return f(*args, **kwargs)
    return decorated_function
# END CUSTOMIZE DECORATOR

# START VIEWS
@app.route('/error/<string:code>')
def error(code, msg=None):
    supported_code = ('400', '401', '404', '500')
    if code in supported_code:
        return render_template('%s.html' % code, msg=msg), int(code)
    else:
        return render_template('404.html'), 404


@app.route('/login', methods=['GET', 'POST'])
@login_manager.unauthorized_handler
def login():

    if g.user is not None and current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'GET':
        return render_template('login.html')
    
    # process login
    username = request.form['username']
    password = request.form['password']
    auth_method = request.form['auth_method'] if 'auth_method' in request.form else 'LOCAL'

    # addition fields for registration case
    firstname = request.form['firstname'] if 'firstname' in request.form else None
    lastname = request.form['lastname'] if 'lastname' in request.form else None
    email = request.form['email'] if 'email' in request.form else None
    
    if None in [firstname, lastname, email]:
        #login case
        remember_me = False
        if 'remember' in request.form:
            remember_me = True

        user = User(username=username, password=password, plain_text_password=password)

        try:
            auth = user.is_validate(method=auth_method)
            if auth == False:
                return render_template('login.html', error='Invalid credentials')
        except Exception, e:
            error = e.message['desc'] if 'desc' in e.message else e
            return render_template('login.html', error=error)

        login_user(user, remember = remember_me)
        return redirect(request.args.get('next') or url_for('index'))
    else:
        # registration case
        user = User(username=username, plain_text_password=password, firstname=firstname, lastname=lastname, email=email)
        try:
            result = user.create_local_user()
            if result == True:
                return render_template('login.html')
            else:
                return render_template('login.html', error=result)
        except Exception, e:
            error = e.message['desc'] if 'desc' in e.message else e
            return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login')) 


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    d = Domain().update()
    if current_user.role.name == 'Administrator':
        domains = Domain.query.all()
    else:
        domains = User(id=current_user.id).get_domain()

    return render_template('dashboard.html', domains=domains)


@app.route('/domain/<string:domain_name>', methods=['GET', 'POST'])
@app.route('/domain', methods=['GET', 'POST'])
@login_required
def domain(domain_name):
    r = Record()
    domain = Domain.query.filter(Domain.name == domain_name).first()
    if domain:
        # query domain info from PowerDNS API
        zone_info = r.get_record_data(domain.name)
        if zone_info:
            jrecords = zone_info['records']
        else:
            # can not get any record, API server might be down
            return redirect(url_for('error', code=500))

        records = []
        for jr in jrecords:
            if jr['type'] in app.config['RECORDS_ALLOW_EDIT']:
                record = Record(name=jr['name'], type=jr['type'], status='Disabled' if jr['disabled'] else 'Active', ttl=jr['ttl'], data=jr['content'])
                records.append(record)
        return render_template('domain.html', domain=domain, records=records, editable_records=app.config['RECORDS_ALLOW_EDIT'])
    else:
        return redirect(url_for('error', code=404))


@app.route('/admin/domain/add', methods=['GET', 'POST'])
@login_required
@admin_role_required
def domain_add():
    if request.method == 'POST':
        try:
            domain_name = request.form.getlist('domain_name')[0]
            domain_type = request.form.getlist('radio_type')[0]
            soa_edit_api = request.form.getlist('radio_type_soa_edit_api')[0]

            if ' ' in domain_name or not domain_name or not domain_type:
                return render_template('400.html', msg="Please correct your input"), 400

            if domain_type == 'slave':
                if request.form.getlist('domain_master_address'):
                    domain_master_string = request.form.getlist('domain_master_address')[0]
                    domain_master_string = domain_master_string.replace(' ','')
                    domain_master_ips = domain_master_string.split(',')
            else:
                domain_master_ips = []
            d = Domain()
            result = d.add(domain_name=domain_name, domain_type=domain_type, soa_edit_api=soa_edit_api, domain_master_ips=domain_master_ips)
            if result['status'] == 'ok':
                history = History(msg='Add domain %s' % domain_name, detail=str({'domain_type': domain_type, 'domain_master_ips': domain_master_ips}), created_by=current_user.username)
                history.add()
                return redirect(url_for('dashboard'))
            else:
                return render_template('400.html', msg=result['msg']), 400
        except:
            return redirect(url_for('error', code=500))
    return render_template('domain_add.html')


@app.route('/admin/domain/<string:domain_name>/delete', methods=['GET'])
@login_required
@admin_role_required
def domain_delete(domain_name):
    d = Domain()
    result = d.delete(domain_name)
    
    if result['status'] == 'error':
        return redirect(url_for('error', code=500))

    history = History(msg='Delete domain %s' % domain_name, created_by=current_user.username)
    history.add()

    return redirect(url_for('dashboard'))


@app.route('/admin/domain/<string:domain_name>/manage', methods=['GET', 'POST'])
@login_required
@admin_role_required
def domain_management(domain_name):
    if request.method == 'GET':
        domain = Domain.query.filter(Domain.name == domain_name).first()
        if not domain:
            return redirect(url_for('error', code=404))
        users = User.query.all()

        # get list of user ids to initilize selection data
        d = Domain(name=domain_name)
        domain_user_ids = d.get_user()

        return render_template('domain_management.html', domain=domain, users=users, domain_user_ids=domain_user_ids)

    if request.method == 'POST':
        # username in right column
        new_user_list = request.form.getlist('domain_multi_user[]')

        # get list of user ids to compare
        d = Domain(name=domain_name)
        domain_user_ids = d.get_user()

        # grant/revoke user privielges 
        d.grant_privielges(new_user_list)

        history = History(msg='Change domain %s access control' % domain_name, detail=str({'user_has_access': new_user_list}), created_by=current_user.username)
        history.add()

        return redirect(url_for('domain_management', domain_name=domain_name))


@app.route('/domain/<string:domain_name>/apply', methods=['POST'], strict_slashes=False)
@login_required
def record_apply(domain_name):
    """
    example jdata: {u'record_ttl': u'1800', u'record_type': u'CNAME', u'record_name': u'test4', u'record_status': u'Active', u'record_data': u'duykhanh.me'}
    """
    #TODO: filter removed records / name modified records.
    try:
        pdata = request.data
        jdata = json.loads(pdata)
        records = []

        for j in jdata:
            record = {
                        "name": domain_name if j['record_name'] in ['@', ''] else j['record_name'] + '.' + domain_name,
                        "type": j['record_type'],
                        "content": j['record_data'],
                        "disabled": True if j['record_status'] == 'Disabled' else False,
                        "name": domain_name if j['record_name'] in ['@', ''] else j['record_name'] + '.' + domain_name,
                        "ttl": int(j['record_ttl']) if j['record_ttl'] else 3600,
                         "type": j['record_type'],
                    }
            records.append(record)

        r = Record()
        result = r.apply(domain_name, records)
        if result['status'] == 'ok':
            history = History(msg='Apply record changes to domain %s' % domain_name, detail=str(records), created_by=current_user.username)
            history.add()
            return make_response(jsonify( result ), 200)
        else:
            return make_response(jsonify( result ), 400)
    except:
        print traceback.format_exc()
        return make_response(jsonify( {'status': 'error', 'msg': 'Error when applying new changes'} ), 500)


@app.route('/domain/<string:domain_name>/update', methods=['POST'], strict_slashes=False)
@login_required
def record_update(domain_name):
    """
    This route is used for domain work as Slave Zone only
    Pulling the records update from its Master
    """
    try:
        pdata = request.data
        jdata = json.loads(pdata)

        domain_name = jdata['domain']
        d = Domain()
        result = d.update_from_master(domain_name)
        if result['status'] == 'ok':
            return make_response(jsonify( {'status': 'ok', 'msg': result['msg']} ), 200)
        else:
            return make_response(jsonify( {'status': 'error', 'msg': result['msg']} ), 500)
    except:
        print traceback.format_exc()
        return make_response(jsonify( {'status': 'error', 'msg': 'Error when applying new changes'} ), 500)


@app.route('/domain/<string:domain_name>/record/<string:record_name>/type/<string:record_type>/delete', methods=['GET'])
@login_required
@admin_role_required
def record_delete(domain_name, record_name, record_type):
    try:
        r = Record(name=record_name, type=record_type)
        result = r.delete(domain=domain_name)
        if result['status'] == 'error':
            print result['msg']
    except:
        print traceback.format_exc()
        return redirect(url_for('error', code=500)), 500 
    return redirect(url_for('domain', domain_name=domain_name))


@app.route('/domain/<string:domain_name>/dnssec', methods=['GET'])
@login_required
def domain_dnssec(domain_name):
    domain = Domain()
    dnssec = domain.get_domain_dnssec(domain_name)
    return make_response(jsonify(dnssec), 200)


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
        uptime = filter(lambda uptime: uptime['name'] == 'uptime', statistics)[0]['value']
    else:
        uptime = 0

    return render_template('admin.html', domains=domains, users=users, configs=configs, statistics=statistics, uptime=uptime, history_number=history_number)


@app.route('/admin/manageuser', methods=['GET', 'POST'])
@login_required
@admin_role_required
def admin_manageuser():
    if request.method == 'GET':
        users = User.query.all()
        return render_template('admin_manageuser.html', users=users)

    if request.method == 'POST':
        #
        # post data should in format
        # {'action': 'delete_user', 'data': 'username'}
        #
        try:
            pdata = request.data
            jdata = json.loads(pdata)
            data = jdata['data']

            if jdata['action'] == 'delete_user':
                user = User(username=data)
                result = user.delete()
                if result:
                    history = History(msg='Delete username %s' % data, created_by=current_user.username)
                    history.add()
                    return make_response(jsonify( { 'status': 'ok', 'msg': 'User has been removed.' } ), 200)
                else:
                    return make_response(jsonify( { 'status': 'error', 'msg': 'Cannot remove user.' } ), 500)
            
            elif jdata['action'] == 'revoke_user_privielges':
                user = User(username=data)
                result = user.revoke_privilege()
                if result:
                    history = History(msg='Revoke %s user privielges' % data, created_by=current_user.username)
                    history.add()
                    return make_response(jsonify( { 'status': 'ok', 'msg': 'Revoked user privielges.' } ), 200)
                else:
                    return make_response(jsonify( { 'status': 'error', 'msg': 'Cannot revoke user privilege.' } ), 500)    
            
            elif jdata['action'] == 'set_admin':
                username = data['username']
                is_admin = data['is_admin']
                user = User(username=username)
                result = user.set_admin(is_admin)
                if result:
                    history = History(msg='Change user role of %s' % username, created_by=current_user.username)
                    history.add()
                    return make_response(jsonify( { 'status': 'ok', 'msg': 'Changed user role successfully.' } ), 200)
                else:
                    return make_response(jsonify( { 'status': 'error', 'msg': 'Cannot change user role.' } ), 500)
            else:
                return make_response(jsonify( { 'status': 'error', 'msg': 'Action not supported.' } ), 400)
        except:
            print traceback.format_exc()
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


@app.route('/user/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    if request.method == 'GET':
        return render_template('user_profile.html')
    if request.method == 'POST':
        # get new profile info
        firstname = request.form['firstname'] if 'firstname' in request.form else ''
        lastname = request.form['lastname'] if 'lastname' in request.form else ''
        email = request.form['email'] if 'email' in request.form else ''
        new_password = request.form['password'] if 'password' in request.form else ''

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

        return render_template('user_profile.html')


@app.route('/user/avatar/<string:filename>')
def user_avatar(filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_DIR'], 'avatar'), filename)


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    return redirect(url_for('dashboard')) 

# END VIEWS

