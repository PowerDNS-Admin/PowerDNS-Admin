import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pyotp

from powerdnsadmin.lib.password_login import register_otp_failure
from powerdnsadmin.models.base import db
from powerdnsadmin.models.history import History
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
        account.otp_failed_attempts = 0
        account.otp_locked_until = None
        account.otp_lockouts = 0
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


def _lock_otp(app, username):
    with app.app_context():
        account = User.query.filter_by(username=username).one()
        account.otp_failed_attempts = 5
        account.otp_locked_until = datetime(2099, 1, 1)
        db.session.commit()


def test_profile_cannot_disable_mfa_while_the_account_is_locked(
        app, client, initial_data, test_admin_user):
    login(client, app)
    secret = 'JBSWY3DPEHPK3PXP'
    set_otp(app, test_admin_user, secret)
    _lock_otp(app, test_admin_user)
    try:
        profile = client.get('/user/profile')
        refused = client.post(
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
        assert refused.status_code == 400
        assert 'Too many authentication attempts' in refused.get_json()['msg']
        with app.app_context():
            admin = User.query.filter_by(username=test_admin_user).one()
            assert admin.otp_secret == secret
            assert admin.otp_last_used is None
            assert admin.otp_failed_attempts == 5
    finally:
        set_otp(app, test_admin_user, '')


def test_rejected_profile_codes_use_the_shared_lock(
        app, client, initial_data, test_admin_user):
    login(client, app)
    secret = 'JBSWY3DPEHPK3PXP'
    set_otp(app, test_admin_user, secret)
    try:
        profile = client.get('/user/profile')
        for _ in range(5):
            refused = client.post(
                '/user/profile',
                json={
                    'action': 'enable_otp',
                    'data': {'enable_otp': False, 'otp_token': '000000'},
                    '_csrf_token': csrf_token(profile),
                },
            )
            assert refused.status_code == 400
        assert 'Too many authentication attempts' in refused.get_json()['msg']
        with app.app_context():
            admin = User.query.filter_by(username=test_admin_user).one()
            assert admin.otp_failed_attempts == 5
            assert admin.otp_locked_until is not None
            assert admin.otp_secret == secret
    finally:
        set_otp(app, test_admin_user, '')


def test_administrator_cannot_remove_own_mfa_while_locked(
        app, client, initial_data, test_admin_user):
    login(client, app)
    secret = 'JBSWY3DPEHPK3PXP'
    set_otp(app, test_admin_user, secret)
    _lock_otp(app, test_admin_user)
    try:
        page = client.get('/admin/manage-user')
        token_match = re.search(rb"'_csrf_token': '([^']+)'", page.data)
        assert token_match is not None
        refused = client.post(
            '/admin/manage-user',
            json={
                'action': 'user_otp_disable',
                'data': test_admin_user,
                'otp_token': pyotp.TOTP(secret).now(),
                '_csrf_token': token_match.group(1).decode('utf-8'),
            },
        )
        assert refused.status_code == 400
        assert 'Too many authentication attempts' in refused.get_json()['msg']
        with app.app_context():
            admin = User.query.filter_by(username=test_admin_user).one()
            assert admin.otp_secret == secret
            assert admin.otp_last_used is None
    finally:
        set_otp(app, test_admin_user, '')


def test_concurrent_otp_failures_all_count(
        app, initial_data, test_admin_user):
    secret = 'JBSWY3DPEHPK3PXP'
    set_otp(app, test_admin_user, secret)

    def fail_once(_):
        with app.app_context():
            try:
                account = User.query.filter_by(username=test_admin_user).one()
                register_otp_failure(account)
            finally:
                db.session.remove()

    try:
        with ThreadPoolExecutor(max_workers=5) as pool:
            list(pool.map(fail_once, range(5)))
        with app.app_context():
            account = User.query.filter_by(username=test_admin_user).one()
            assert account.otp_failed_attempts == 5
            assert account.otp_locked_until is not None
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


def test_enrolled_mfa_secret_is_not_disclosed_to_the_session(
        app, client, initial_data, test_admin_user):
    login(client, app)
    secret = 'JBSWY3DPEHPK3PXP'
    set_otp(app, test_admin_user, secret)
    try:
        with app.app_context():
            account = User.query.filter_by(username=test_admin_user).one()
            account.otp_last_used = 1
            db.session.commit()

        confirmed = client.get('/user/profile')
        assert confirmed.status_code == 200
        assert secret.encode() not in confirmed.data
        assert b'Your secret key is' not in confirmed.data
        hidden = client.get('/user/qrcode')
        assert hidden.status_code == 404
        assert secret.encode() not in hidden.data

        with app.app_context():
            account = User.query.filter_by(username=test_admin_user).one()
            account.otp_last_used = None
            db.session.commit()

        enrolling = client.get('/user/profile')
        assert secret.encode() in enrolling.data
        qrcode = client.get('/user/qrcode')
        assert qrcode.status_code == 200
        assert qrcode.mimetype == 'image/svg+xml'
    finally:
        set_otp(app, test_admin_user, '')


def test_password_change_rejects_the_pending_mfa_challenge(
        app, client, initial_data, test_admin_user):
    secret = 'JBSWY3DPEHPK3PXP'
    set_otp(app, test_admin_user, secret)
    with app.app_context():
        original_version = User.query.filter_by(
            username=test_admin_user).one().session_version or 0
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

        replacement = 'replacement-admin-password'
        with app.app_context():
            account = User.query.filter_by(username=test_admin_user).one()
            account.password = account.get_hashed_password(
                replacement).decode('utf-8')
            account.rotate_session_version()
            db.session.commit()

        rejected = client.post(
            '/login',
            data={
                'otptoken': pyotp.TOTP(secret).now(),
                '_csrf_token': csrf_token(password_response),
            },
        )
        assert rejected.status_code == 200
        assert b'sign-in code expired' in rejected.data
        assert b'name="otptoken"' not in rejected.data
        profile = client.get('/user/profile')
        assert profile.status_code == 302
        assert '/login' in profile.headers['Location']

        old_password = client.post(
            '/login',
            data={
                'username': app.config['TEST_ADMIN_USER'],
                'password': app.config['TEST_ADMIN_PASSWORD'],
                'auth_method': 'LOCAL',
                '_csrf_token': csrf_token(rejected),
            },
        )
        assert b'Invalid credentials' in old_password.data

        resumed = client.post(
            '/login',
            data={
                'username': app.config['TEST_ADMIN_USER'],
                'password': replacement,
                'auth_method': 'LOCAL',
                '_csrf_token': csrf_token(old_password),
            },
        )
        assert b'name="otptoken"' in resumed.data
        completed = client.post(
            '/login',
            data={
                'otptoken': pyotp.TOTP(secret).now(),
                '_csrf_token': csrf_token(resumed),
            },
        )
        assert completed.status_code == 302
    finally:
        set_otp(app, test_admin_user, '')
        with app.app_context():
            account = User.query.filter_by(username=test_admin_user).one()
            account.password = account.get_hashed_password(
                app.config['TEST_ADMIN_PASSWORD']).decode('utf-8')
            account.session_version = original_version
            account.otp_secret = ''
            account.otp_last_used = None
            db.session.commit()


def test_pending_mfa_challenge_without_a_session_version_is_rejected(
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
        assert b'name="otptoken"' in password_response.data
        with client.session_transaction() as session:
            session.pop('pending_totp_session_version', None)

        rejected = client.post(
            '/login',
            data={
                'otptoken': pyotp.TOTP(secret).now(),
                '_csrf_token': csrf_token(password_response),
            },
        )
        assert rejected.status_code == 200
        assert b'sign-in code expired' in rejected.data
        profile = client.get('/user/profile')
        assert profile.status_code == 302
        assert '/login' in profile.headers['Location']
    finally:
        set_otp(app, test_admin_user, '')


def _setting_value(app, name, value):
    with app.app_context():
        Setting().set(name, value)


def test_basic_auth_cannot_skip_forced_mfa_enrollment(
        app, client, initial_data, basic_auth_admin_headers, test_admin_user):
    _setting_value(app, 'otp_force', 'True')
    _setting_value(app, 'otp_field_enabled', 'True')
    set_otp(app, test_admin_user, '')
    try:
        denied = client.get(
            '/api/v1/pdnsadmin/users', headers=basic_auth_admin_headers)
        assert denied.status_code == 401
        dyndns = client.get('/nic/update', headers=basic_auth_admin_headers)
        assert dyndns.status_code == 401
        with app.app_context():
            account = User.query.filter_by(username=test_admin_user).one()
            assert not account.otp_secret

        secret = 'JBSWY3DPEHPK3PXP'
        set_otp(app, test_admin_user, secret)
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
        _setting_value(app, 'otp_force', 'False')
        _setting_value(app, 'otp_field_enabled', 'True')


def test_rejected_otp_attempts_are_shared_across_password_logins(
        app, client, initial_data, basic_auth_admin_headers, test_admin_user):
    secret = 'JBSWY3DPEHPK3PXP'
    set_otp(app, test_admin_user, secret)
    wrong = {**basic_auth_admin_headers, 'X-OTP': '000000'}
    try:
        for _ in range(3):
            assert client.get(
                '/api/v1/pdnsadmin/users', headers=wrong).status_code == 401
        assert client.get('/nic/update', headers=wrong).status_code == 401

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
        assert b'name="otptoken"' in challenge.data
        locked = client.post(
            '/login',
            data={
                'otptoken': '000000',
                '_csrf_token': csrf_token(challenge),
            },
        )
        assert b'Too many authentication attempts' in locked.data

        still_locked = client.get(
            '/api/v1/pdnsadmin/users',
            headers={
                **basic_auth_admin_headers,
                'X-OTP': pyotp.TOTP(secret).now(),
            },
        )
        assert still_locked.status_code == 401

        with app.app_context():
            account = User.query.filter_by(username=test_admin_user).one()
            account.otp_locked_until = datetime(2000, 1, 1)
            db.session.commit()

        unlocked = client.get(
            '/api/v1/pdnsadmin/users',
            headers={
                **basic_auth_admin_headers,
                'X-OTP': pyotp.TOTP(secret).now(),
            },
        )
        assert unlocked.status_code == 200
    finally:
        set_otp(app, test_admin_user, '')


def _submit_wrong_login_codes(client, app, count):
    page = client.get('/login')
    response = client.post(
        '/login',
        data={
            'username': app.config['TEST_ADMIN_USER'],
            'password': app.config['TEST_ADMIN_PASSWORD'],
            'auth_method': 'LOCAL',
            '_csrf_token': csrf_token(page),
        },
    )
    assert b'name="otptoken"' in response.data
    for _ in range(count):
        response = client.post(
            '/login',
            data={
                'otptoken': '000000',
                '_csrf_token': csrf_token(response),
            },
        )
    return response


def _otp_failure_rows(app, username, after_id):
    with app.app_context():
        rows = History.query.filter(
            History.id > after_id,
            History.msg.like(
                'User {0} authentication failed%'.format(username)),
        ).order_by(History.id).all()
        return [(row.msg, json.loads(row.detail)) for row in rows]


def test_login_failures_record_the_counter_and_staggered_unlock(
        app, client, initial_data, test_admin_user):
    secret = 'JBSWY3DPEHPK3PXP'
    set_otp(app, test_admin_user, secret)
    try:
        with app.app_context():
            after_id = db.session.query(db.func.max(History.id)).scalar() or 0
        locked = _submit_wrong_login_codes(client, app, 5)
        assert b'Too many authentication attempts. Try again later.' in locked.data
        recorded = _otp_failure_rows(app, test_admin_user, after_id)
        assert [detail['attempt'] for _, detail in recorded] == [1, 2, 3, 4, 5]
        assert all(detail['path'] == '/login' for _, detail in recorded)
        assert 'attempt 1 of 5' in recorded[0][0]
        assert 'locked' not in recorded[0][0]
        assert 'attempt 5 of 5, locked for 5 minutes until' in recorded[4][0]
        assert recorded[4][1]['locked_until']
        with app.app_context():
            account = User.query.filter_by(username=test_admin_user).one()
            remaining = (account.otp_locked_until - datetime.utcnow()).total_seconds()
            assert account.otp_lockouts == 1
            assert 4 * 60 < remaining < 6 * 60
            account.otp_locked_until = datetime(2000, 1, 1)
            db.session.commit()
            after_id = db.session.query(db.func.max(History.id)).scalar() or 0

        locked_again = _submit_wrong_login_codes(client, app, 5)
        assert b'Too many authentication attempts. Try again later.' in locked_again.data
        recorded = _otp_failure_rows(app, test_admin_user, after_id)
        assert 'locked for 15 minutes until' in recorded[-1][0]
        with app.app_context():
            account = User.query.filter_by(username=test_admin_user).one()
            until = account.otp_locked_until
            remaining = (until - datetime.utcnow()).total_seconds()
            assert account.otp_lockouts == 2
            assert 14 * 60 < remaining < 16 * 60

        repeated = client.post(
            '/login',
            data={
                'username': app.config['TEST_ADMIN_USER'],
                'password': app.config['TEST_ADMIN_PASSWORD'],
                'auth_method': 'LOCAL',
                '_csrf_token': csrf_token(locked_again),
            },
        )
        assert b'Too many authentication attempts. Try again later.' in repeated.data
        with app.app_context():
            account = User.query.filter_by(username=test_admin_user).one()
            assert account.otp_lockouts == 2
            assert account.otp_locked_until == until
            latest = History.query.filter(
                History.msg.like(
                    'User {0} authentication failed%'.format(test_admin_user)),
            ).order_by(History.id.desc()).first()
            assert 'attempt 5 of 5, locked until' in latest.msg
            assert 'locked for' not in latest.msg
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
