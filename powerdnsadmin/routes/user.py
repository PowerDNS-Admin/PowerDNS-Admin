import datetime
from flask import Blueprint, request, render_template, make_response, jsonify, redirect, url_for, g, session, current_app
from flask_login import current_user, login_required, login_manager

from ..models.user import User, Anonymous
from ..models.setting import Setting

user_bp = Blueprint('user',
                    __name__,
                    template_folder='templates',
                    url_prefix='/user')


@user_bp.before_request
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


@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'GET':
        return render_template('user_profile.html')
    if request.method == 'POST':
        if session['authentication_type'] == 'LOCAL':
            firstname = request.form.get('firstname', '').strip()
            lastname = request.form.get('lastname', '').strip()
            email = request.form.get('email', '').strip()
            new_password = request.form.get('password', '')
        else:
            firstname = lastname = email = new_password = ''
            current_app.logger.warning(
                'Authenticated externally. User {0} information will not allowed to update the profile'
                .format(current_user.username))

        if request.data:
            jdata = request.json
            data = jdata['data']
            if jdata['action'] == 'enable_otp':
                if session['authentication_type'] in ['LOCAL', 'LDAP']:
                    enable_otp = data['enable_otp']
                    user = User(username=current_user.username)
                    user.update_profile(enable_otp=enable_otp)
                    return make_response(
                        jsonify({
                            'status':
                            'ok',
                            'msg':
                            'Change OTP Authentication successfully. Status: {0}'
                            .format(enable_otp)
                        }), 200)
                else:
                    return make_response(
                        jsonify({
                            'status':
                            'error',
                            'msg':
                            'User {0} is externally. You are not allowed to update the OTP'
                            .format(current_user.username)
                        }), 400)

        user = User(username=current_user.username,
                    plain_text_password=new_password,
                    firstname=firstname,
                    lastname=lastname,
                    email=email,
                    reload_info=False)
        user.update_profile()

        return render_template('user_profile.html')


@user_bp.route('/qrcode')
@login_required
def qrcode():
    if not current_user:
        return redirect(url_for('index'))

    return current_user.get_qrcode_value(), 200, {
        'Content-Type': 'image/svg+xml',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }