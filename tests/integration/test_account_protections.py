import re

import pyotp

from powerdnsadmin.models.base import db
from powerdnsadmin.models.setting import Setting
from powerdnsadmin.models.user import User


def csrf_token(response):
    match = re.search(
        rb'name="_csrf_token" value="([^"]+)"',
        response.data,
    )
    assert match is not None
    return match.group(1).decode('utf-8')


def login(client, app, username=None, password=None):
    page = client.get('/login')
    response = client.post(
        '/login',
        data={
            'username': username or app.config['TEST_ADMIN_USER'],
            'password': password or app.config['TEST_ADMIN_PASSWORD'],
            'auth_method': 'LOCAL',
            '_csrf_token': csrf_token(page),
        },
    )
    assert response.status_code == 302
    return response


def set_otp(app, username, secret):
    with app.app_context():
        account = User.query.filter_by(username=username).one()
        account.otp_secret = secret
        account.otp_last_used = None
        db.session.commit()
        return account.id


def test_browser_and_api_basic_auth_honor_mfa(
        app, client, initial_data, test_admin_user, basic_auth_admin_headers):
    secret = 'JBSWY3DPEHPK3PXP'
    set_otp(app, test_admin_user, secret)
    try:
        blocked = client.get(
            '/user/profile', headers=basic_auth_admin_headers)
        assert blocked.status_code == 302
        assert '/login' in blocked.headers['Location']

        denied = client.get(
            '/api/v1/pdnsadmin/users', headers=basic_auth_admin_headers)
        assert denied.status_code == 401

        allowed = client.get(
            '/api/v1/pdnsadmin/users',
            headers={
                **basic_auth_admin_headers,
                'X-OTP': pyotp.TOTP(secret).now(),
            },
        )
        assert allowed.status_code == 200
    finally:
        set_otp(app, test_admin_user, '')


def test_api_self_service_cannot_replace_the_mfa_secret(
        app, client, initial_data, test_admin_user, test_user,
        basic_auth_admin_headers):
    secret = 'JBSWY3DPEHPK3PXP'
    admin_id = set_otp(app, test_admin_user, secret)
    try:
        response = client.put(
            '/api/v1/pdnsadmin/users/{0}'.format(admin_id),
            headers={
                **basic_auth_admin_headers,
                'X-OTP': pyotp.TOTP(secret).now(),
            },
            json={'otp_secret': ''},
        )
        assert response.status_code == 401
        assert 'current code' in response.get_json()['msg']
        with app.app_context():
            admin = db.session.get(User, admin_id)
            assert admin.otp_secret == secret
    finally:
        set_otp(app, test_admin_user, '')

    user_id = set_otp(app, test_user, secret)
    response = client.put(
        '/api/v1/pdnsadmin/users/{0}'.format(user_id),
        headers=basic_auth_admin_headers,
        json={'otp_secret': ''},
    )
    assert response.status_code == 204
    with app.app_context():
        account = db.session.get(User, user_id)
        assert account.otp_secret == ''


def test_profile_cannot_disable_mfa_without_the_current_code(
        app, client, initial_data, test_admin_user):
    login(client, app)
    secret = 'JBSWY3DPEHPK3PXP'
    set_otp(app, test_admin_user, secret)
    try:
        profile = client.get('/user/profile')
        refused = client.post(
            '/user/profile',
            json={
                'action': 'enable_otp',
                'data': {'enable_otp': False},
                '_csrf_token': csrf_token(profile),
            },
        )
        assert refused.status_code == 400
        with app.app_context():
            admin = User.query.filter_by(username=test_admin_user).one()
            assert admin.otp_secret == secret

        disabled = client.post(
            '/user/profile',
            json={
                'action': 'enable_otp',
                'data': {
                    'enable_otp': False,
                    'otp_token': pyotp.TOTP(secret).now(),
                },
                '_csrf_token': csrf_token(profile),
            },
        )
        assert disabled.status_code == 200
        with app.app_context():
            admin = User.query.filter_by(username=test_admin_user).one()
            assert admin.otp_secret == ''
    finally:
        set_otp(app, test_admin_user, '')


def test_password_change_revokes_the_other_session(
        app, initial_data, test_admin_user):
    first = app.test_client()
    second = app.test_client()
    login(first, app)
    login(second, app)
    try:
        profile = first.get('/user/profile')
        updated = first.post(
            '/user/profile',
            data={
                'firstname': '',
                'lastname': '',
                'email': '',
                'password': 'replacement-admin-password',
                '_csrf_token': csrf_token(profile),
            },
        )
        assert updated.status_code == 200

        assert first.get('/user/profile').status_code == 200
        other = second.get('/user/profile')
        assert other.status_code == 302
        assert '/login' in other.headers['Location']
    finally:
        with app.app_context():
            admin = User.query.filter_by(username=test_admin_user).one()
            admin.password = admin.get_hashed_password(
                app.config['TEST_ADMIN_PASSWORD']).decode('utf-8')
            admin.session_version = 0
            db.session.commit()


def test_otp_challenge_expires_and_stops_after_repeated_failures(
        app, client, initial_data, test_admin_user):
    secret = 'JBSWY3DPEHPK3PXP'
    set_otp(app, test_admin_user, secret)
    try:
        page = client.get('/login')
        password_response = client.post(
            '/login',
            data={
                'username': app.config['TEST_ADMIN_USER'],
                'password': app.config['TEST_ADMIN_PASSWORD'],
                'auth_method': 'LOCAL',
                '_csrf_token': csrf_token(page),
            },
        )
        assert password_response.status_code == 200
        assert b'name="otptoken"' in password_response.data

        with client.session_transaction() as session:
            session['pending_totp_deadline'] = 1

        expired = client.post(
            '/login',
            data={
                'otptoken': pyotp.TOTP(secret).now(),
                '_csrf_token': csrf_token(password_response),
            },
        )
        assert expired.status_code == 200
        assert b'sign-in code expired' in expired.data
        with client.session_transaction() as session:
            assert 'pending_totp_user_id' not in session

        page = client.get('/login')
        challenge = client.post(
            '/login',
            data={
                'username': app.config['TEST_ADMIN_USER'],
                'password': app.config['TEST_ADMIN_PASSWORD'],
                'auth_method': 'LOCAL',
                '_csrf_token': csrf_token(page),
            },
        )
        for _ in range(4):
            challenge = client.post(
                '/login',
                data={
                    'otptoken': '000000',
                    '_csrf_token': csrf_token(challenge),
                },
            )
            assert b'Invalid credentials' in challenge.data
            assert b'name="otptoken"' in challenge.data

        locked = client.post(
            '/login',
            data={
                'otptoken': '000000',
                '_csrf_token': csrf_token(challenge),
            },
        )
        assert b'Too many authentication attempts' in locked.data
        assert b'name="otptoken"' not in locked.data
        with client.session_transaction() as session:
            assert 'pending_totp_user_id' not in session
    finally:
        set_otp(app, test_admin_user, '')


def test_maintenance_blocks_an_authenticated_api_user(
        app, client, initial_data, basic_auth_user_headers,
        basic_auth_admin_headers, test_user):
    with app.app_context():
        setting = Setting.query.filter_by(name='maintenance').first()
        if setting is None:
            setting = Setting(name='maintenance', value='True')
            db.session.add(setting)
        else:
            setting.value = 'True'
        db.session.commit()
    try:
        blocked = client.get(
            '/api/v1/pdnsadmin/users/{0}'.format(test_user),
            headers=basic_auth_user_headers,
        )
        assert blocked.status_code == 503
        assert blocked.get_json()['msg'] == 'Site is in maintenance mode'

        allowed = client.get(
            '/api/v1/pdnsadmin/users',
            headers=basic_auth_admin_headers,
        )
        assert allowed.status_code == 200
    finally:
        with app.app_context():
            setting = Setting.query.filter_by(name='maintenance').one()
            setting.value = 'False'
            db.session.commit()
