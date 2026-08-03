import re

import pyotp

from powerdnsadmin.models.base import db
from powerdnsadmin.models.user import User


def csrf_token(response):
    match = re.search(
        rb'name="_csrf_token" value="([^"]+)"',
        response.data,
    )
    assert match is not None
    return match.group(1).decode('utf-8')


def session_id(client):
    cookie = client.get_cookie('session')
    assert cookie is not None
    return cookie.value


def test_login_page_does_not_refresh_an_idle_session(
        client, initial_data):
    login_page = client.get('/login')

    assert login_page.status_code == 200
    assert b'http-equiv="refresh"' not in login_page.data.lower()


def test_login_only_prompts_for_otp_when_user_has_totp_configured(
        app, client, initial_data, test_admin_user, monkeypatch):
    login_page = client.get('/login')
    assert b'name="otptoken"' not in login_page.data

    # Production secrets are 16 characters (the width of User.otp_secret).
    otp_secret = 'JBSWY3DPEHPK3PXP'
    current_time = 2_000_000_000
    monkeypatch.setattr(
        'powerdnsadmin.models.user.time.time', lambda: current_time)
    with app.app_context():
        administrator = User.query.filter_by(username=test_admin_user).one()
        administrator.otp_secret = otp_secret
        db.session.commit()

    try:
        password_response = client.post(
            '/login',
            data={
                'username': app.config['TEST_ADMIN_USER'],
                'password': app.config['TEST_ADMIN_PASSWORD'],
                'auth_method': 'LOCAL',
                '_csrf_token': csrf_token(login_page),
            },
        )

        assert password_response.status_code == 200
        assert b'name="otptoken"' in password_response.data
        assert b'name="password"' not in password_response.data

        otp_token = pyotp.TOTP(otp_secret).at(current_time)
        otp_response = client.post(
            '/login',
            data={
                'otptoken': otp_token,
                '_csrf_token': csrf_token(password_response),
            },
        )

        assert otp_response.status_code == 302
        assert otp_response.headers['Location'].endswith('/login')

        client.get('/logout')
        replay_login_page = client.get('/login')
        replay_password_response = client.post(
            '/login',
            data={
                'username': app.config['TEST_ADMIN_USER'],
                'password': app.config['TEST_ADMIN_PASSWORD'],
                'auth_method': 'LOCAL',
                '_csrf_token': csrf_token(replay_login_page),
            },
        )
        replay_response = client.post(
            '/login',
            data={
                'otptoken': otp_token,
                '_csrf_token': csrf_token(replay_password_response),
            },
        )

        assert replay_response.status_code == 200
        assert b'Invalid credentials' in replay_response.data

        # Two steps away is outside the tolerated +/-1 step window, so this
        # must be rejected regardless of the replay-claim state.
        expired_token = pyotp.TOTP(otp_secret).at(current_time - 60)
        expired_response = client.post(
            '/login',
            data={
                'otptoken': expired_token,
                '_csrf_token': csrf_token(replay_response),
            },
        )

        assert expired_response.status_code == 200
        assert b'Invalid credentials' in expired_response.data
    finally:
        with app.app_context():
            administrator = User.query.filter_by(
                username=test_admin_user).one()
            administrator.otp_secret = ''
            administrator.otp_last_used = None
            db.session.commit()


def test_login_accepts_totp_token_from_an_adjacent_time_step(
        app, client, initial_data, test_admin_user, monkeypatch):
    otp_secret = 'JBSWY3DPEHPK3PXP'
    current_time = 2_000_000_000
    monkeypatch.setattr(
        'powerdnsadmin.models.user.time.time', lambda: current_time)
    with app.app_context():
        administrator = User.query.filter_by(username=test_admin_user).one()
        administrator.otp_secret = otp_secret
        db.session.commit()

    try:
        login_page = client.get('/login')
        password_response = client.post(
            '/login',
            data={
                'username': app.config['TEST_ADMIN_USER'],
                'password': app.config['TEST_ADMIN_PASSWORD'],
                'auth_method': 'LOCAL',
                '_csrf_token': csrf_token(login_page),
            },
        )

        # Simulates an authenticator app running one 30-second step ahead of
        # the server's clock -- still inside the tolerated window.
        drifted_token = pyotp.TOTP(otp_secret).at(current_time + 30)
        otp_response = client.post(
            '/login',
            data={
                'otptoken': drifted_token,
                '_csrf_token': csrf_token(password_response),
            },
        )

        assert otp_response.status_code == 302
        assert otp_response.headers['Location'].endswith('/login')
    finally:
        with app.app_context():
            administrator = User.query.filter_by(
                username=test_admin_user).one()
            administrator.otp_secret = ''
            administrator.otp_last_used = None
            db.session.commit()


def test_successful_login_rotates_session_and_remains_valid_for_dashboard_v2(
        app, client, initial_data, test_admin_user):
    login_page = client.get('/login')
    anonymous_session_id = session_id(client)

    login_response = client.post(
        '/login',
        data={
            'username': app.config['TEST_ADMIN_USER'],
            'password': app.config['TEST_ADMIN_PASSWORD'],
            'auth_method': 'LOCAL',
            '_csrf_token': csrf_token(login_page),
        },
    )

    assert login_response.status_code == 302
    assert session_id(client) != anonymous_session_id

    dashboard_response = client.get('/dashboard/v2/')
    assert dashboard_response.status_code == 200
    assert b'login-card-body' not in dashboard_response.data


def test_expired_login_csrf_clears_authentication_and_returns_fresh_form(
        app, client, initial_data, test_admin_user):
    login_page = client.get('/login')
    assert login_page.status_code == 200
    expired_token = csrf_token(login_page)

    with app.app_context():
        administrator_id = User.query.filter_by(
            username=test_admin_user).one().id

    with client.session_transaction() as session:
        session['_user_id'] = str(administrator_id)
        session['_fresh'] = True
        session['authentication_type'] = 'LOCAL'
        session['next'] = '/admin/manage-user'
        session.pop('_csrf_token', None)

    expired_response = client.post(
        '/login',
        data={
            'username': app.config['TEST_ADMIN_USER'],
            'password': app.config['TEST_ADMIN_PASSWORD'],
            'auth_method': 'LOCAL',
            '_csrf_token': expired_token,
        },
    )

    assert expired_response.status_code == 403
    assert b'Your login form expired. Please try again.' in (
        expired_response.data)
    assert b'Oops! Access Denied' not in expired_response.data
    fresh_token = csrf_token(expired_response)
    assert fresh_token != expired_token

    with client.session_transaction() as session:
        assert '_user_id' not in session
        assert 'user_id' not in session
        assert 'authentication_type' not in session
        assert 'next' not in session

    login_response = client.post(
        '/login',
        data={
            'username': app.config['TEST_ADMIN_USER'],
            'password': app.config['TEST_ADMIN_PASSWORD'],
            'auth_method': 'LOCAL',
            '_csrf_token': fresh_token,
        },
    )

    assert login_response.status_code == 302
    assert login_response.headers['Location'].endswith('/login')

    dashboard_redirect = client.get('/login')
    assert dashboard_redirect.status_code == 302
    assert dashboard_redirect.headers['Location'].rstrip('/').endswith(
        '/dashboard')


def test_expired_registration_csrf_does_not_create_user_and_returns_fresh_form(
        app, client, initial_data, test_admin_user, monkeypatch):
    monkeypatch.setattr(
        'powerdnsadmin.routes.index.captcha.validate',
        lambda: True,
    )

    registration_page = client.get('/register')
    assert registration_page.status_code == 200
    expired_token = csrf_token(registration_page)

    username = 'expired-csrf-registration'
    password = 'ExpiredCsrfRegistrationPassword123!'

    with app.app_context():
        administrator_id = User.query.filter_by(
            username=test_admin_user).one().id

    with client.session_transaction() as session:
        session['_user_id'] = str(administrator_id)
        session['_fresh'] = True
        session['authentication_type'] = 'LOCAL'
        session['next'] = '/admin/manage-user'
        session.pop('_csrf_token', None)

    registration_data = {
        'firstname': 'Expired',
        'lastname': 'Registration',
        'email': 'expired-csrf-registration@example.com',
        'username': username,
        'password': password,
        'rpassword': password,
        '_csrf_token': expired_token,
    }
    expired_response = client.post('/register', data=registration_data)

    assert expired_response.status_code == 403
    assert b'Your registration form expired. Please try again.' in (
        expired_response.data)
    assert b'Oops! Access Denied' not in expired_response.data
    assert username.encode('utf-8') in expired_response.data
    assert password.encode('utf-8') not in expired_response.data
    fresh_token = csrf_token(expired_response)
    assert fresh_token != expired_token

    with app.app_context():
        assert User.query.filter_by(username=username).first() is None

    with client.session_transaction() as session:
        assert '_user_id' not in session
        assert 'user_id' not in session
        assert 'authentication_type' not in session
        assert 'next' not in session

    registration_data['_csrf_token'] = fresh_token
    registration_response = client.post(
        '/register',
        data=registration_data,
    )

    assert registration_response.status_code == 302
    assert registration_response.headers['Location'].endswith('/login')
    with app.app_context():
        assert User.query.filter_by(username=username).one()
