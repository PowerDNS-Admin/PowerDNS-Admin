import qrcode as qrc
import qrcode.image.svg as qrc_svg
from io import BytesIO
from flask import Blueprint, request, render_template, make_response, jsonify, redirect, url_for, current_app, session, g
from flask_login import current_user, login_user, logout_user, login_required

from .base import login_manager
from ..models.user import User
from ..models.role import Role

user_bp = Blueprint('user',
                    __name__,
                    template_folder='templates',
                    url_prefix='/user')


@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'GET':
        return render_template('user_profile.html')
    if request.method == 'POST':
        if session['authentication_type'] == 'LOCAL':
            firstname = request.form[
                'firstname'] if 'firstname' in request.form else ''
            lastname = request.form[
                'lastname'] if 'lastname' in request.form else ''
            email = request.form['email'] if 'email' in request.form else ''
            new_password = request.form[
                'password'] if 'password' in request.form else ''
        else:
            firstname = lastname = email = new_password = ''
            logging.warning(
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

    img = qrc.make(current_user.get_totp_uri(),
                   image_factory=qrc_svg.SvgPathImage)
    stream = BytesIO()
    img.save(stream)
    return stream.getvalue(), 200, {
        'Content-Type': 'image/svg+xml',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }
