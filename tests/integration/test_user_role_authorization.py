import re
from base64 import b64encode

import pyotp
import pytest

from powerdnsadmin.models.base import db
from powerdnsadmin.models.role import Role
from powerdnsadmin.models.setting import Setting
from powerdnsadmin.models.user import User


def basic_auth_headers(username, password):
    credentials = b64encode(
        '{}:{}'.format(username, password).encode('utf-8')
    ).decode('utf-8')
    return {'Authorization': 'Basic {}'.format(credentials)}


def assert_user_role(app, username, role_name):
    with app.app_context():
        user = User.query.filter_by(username=username).one()
        assert user.role.name == role_name


def csrf_token_for_manage_user(client, headers):
    response = client.get('/admin/manage-user', headers=headers)
    assert response.status_code == 200
    token_match = re.search(
        rb"'_csrf_token': '([^']+)'",
        response.data,
    )
    assert token_match is not None
    return token_match.group(1).decode('utf-8'), response


def post_web_role_change(client, headers, username, role_name):
    csrf_token, _ = csrf_token_for_manage_user(client, headers)
    return client.post(
        '/admin/manage-user',
        headers=headers,
        json={
            'action': 'update_user_role',
            'data': {
                'username': username,
                'role_name': role_name,
            },
            '_csrf_token': csrf_token,
        },
    )


@pytest.fixture
def role_security_users(app, initial_data):
    operator_username = 'role-security-operator'
    operator_password = 'OperatorPassword123!'
    target_username = 'role-security-target'
    target_password = 'TargetPassword123!'

    with app.app_context():
        operator = User(
            username=operator_username,
            plain_text_password=operator_password,
            email='role-security-operator@example.com',
        )
        assert operator.create_local_user()['status']
        assert operator.set_role('Operator')['status']

        target = User(
            username=target_username,
            plain_text_password=target_password,
            email='role-security-target@example.com',
        )
        assert target.create_local_user()['status']

        target_id = User.query.filter_by(username=target_username).one().id
        administrator_role_id = Role.query.filter_by(
            name='Administrator').one().id

    yield {
        'operator_username': operator_username,
        'operator_password': operator_password,
        'operator_headers': basic_auth_headers(
            operator_username, operator_password),
        'target_username': target_username,
        'target_headers': basic_auth_headers(
            target_username, target_password),
        'target_id': target_id,
        'administrator_role_id': administrator_role_id,
    }

    with app.app_context():
        for username in (operator_username, target_username):
            user = User.query.filter_by(username=username).first()
            if user is not None:
                db.session.delete(user)
        db.session.commit()


@pytest.mark.parametrize('role_payload', [
    pytest.param({'role_name': 'Administrator'}, id='role_name'),
    pytest.param('role_id', id='role_id'),
])
def test_api_user_cannot_promote_self(
        app, client, role_security_users, role_payload):
    payload = dict(role_payload) if isinstance(role_payload, dict) else {
        role_payload: role_security_users['administrator_role_id'],
    }
    response = client.put(
        '/api/v1/pdnsadmin/users/{}'.format(
            role_security_users['target_id']),
        headers=role_security_users['target_headers'],
        json=payload,
    )

    assert response.status_code == 401
    assert 'own role' in response.get_json()['msg']
    assert_user_role(
        app, role_security_users['target_username'], 'User')


def test_api_user_can_still_update_own_profile(
        app, client, role_security_users):
    response = client.put(
        '/api/v1/pdnsadmin/users/{}'.format(
            role_security_users['target_id']),
        headers=role_security_users['target_headers'],
        json={'firstname': 'Updated safely'},
    )

    assert response.status_code == 204
    with app.app_context():
        target = User.query.filter_by(
            username=role_security_users['target_username']).one()
        assert target.firstname == 'Updated safely'
        assert target.role.name == 'User'


@pytest.mark.parametrize('role_payload', [
    pytest.param({'role_name': 'Administrator'}, id='role_name'),
    pytest.param('role_id', id='role_id'),
])
def test_api_operator_cannot_promote_user(
        app, client, role_security_users, role_payload):
    payload = dict(role_payload) if isinstance(role_payload, dict) else {
        role_payload: role_security_users['administrator_role_id'],
    }
    response = client.put(
        '/api/v1/pdnsadmin/users/{}'.format(
            role_security_users['target_id']),
        headers=role_security_users['operator_headers'],
        json=payload,
    )

    assert response.status_code == 401
    assert 'promote' in response.get_json()['msg']
    assert_user_role(
        app, role_security_users['target_username'], 'User')


def test_api_operator_cannot_modify_administrator(
        app, client, role_security_users, test_admin_user):
    with app.app_context():
        administrator_id = User.query.filter_by(
            username=test_admin_user).one().id

    response = client.put(
        '/api/v1/pdnsadmin/users/{}'.format(administrator_id),
        headers=role_security_users['operator_headers'],
        json={'firstname': 'Not allowed'},
    )

    assert response.status_code == 401
    assert 'modify an Administrator' in response.get_json()['msg']


@pytest.mark.parametrize('role_payload', [
    pytest.param({'role_name': 'Administrator'}, id='role_name'),
    pytest.param('role_id', id='role_id'),
])
def test_api_operator_cannot_create_administrator(
        app, client, role_security_users, role_payload):
    payload = dict(role_payload) if isinstance(role_payload, dict) else {
        role_payload: role_security_users['administrator_role_id'],
    }
    username = 'forbidden-administrator-{}'.format(
        next(iter(payload)).replace('_', '-'))
    payload.update({
        'username': username,
        'plain_text_password': 'ForbiddenPassword123!',
        'email': '{}@example.com'.format(username),
    })

    response = client.post(
        '/api/v1/pdnsadmin/users',
        headers=role_security_users['operator_headers'],
        json=payload,
    )

    assert response.status_code == 401
    with app.app_context():
        assert User.query.filter_by(username=username).first() is None


def test_api_operator_can_assign_operator_role(
        app, client, role_security_users):
    response = client.put(
        '/api/v1/pdnsadmin/users/{}'.format(
            role_security_users['target_id']),
        headers=role_security_users['operator_headers'],
        json={'role_name': 'Operator'},
    )

    assert response.status_code == 204
    assert_user_role(
        app, role_security_users['target_username'], 'Operator')


def test_api_administrator_can_assign_administrator_role(
        app, client, role_security_users, basic_auth_admin_headers):
    response = client.put(
        '/api/v1/pdnsadmin/users/{}'.format(
            role_security_users['target_id']),
        headers=basic_auth_admin_headers,
        json={'role_name': 'Administrator'},
    )

    assert response.status_code == 204
    assert_user_role(
        app, role_security_users['target_username'], 'Administrator')


def test_web_user_cannot_change_own_role(
        app, client, role_security_users):
    response = post_web_role_change(
        client,
        role_security_users['operator_headers'],
        role_security_users['operator_username'],
        'User',
    )

    assert response.status_code == 400
    assert 'own role' in response.get_json()['msg']
    assert_user_role(
        app, role_security_users['operator_username'], 'Operator')


def test_web_operator_cannot_promote_user(
        app, client, role_security_users):
    response = post_web_role_change(
        client,
        role_security_users['operator_headers'],
        role_security_users['target_username'],
        'Administrator',
    )

    assert response.status_code == 400
    assert 'promote' in response.get_json()['msg']
    assert_user_role(
        app, role_security_users['target_username'], 'User')


def test_web_operator_role_menu_excludes_administrator(
        client, role_security_users):
    _, response = csrf_token_for_manage_user(
        client, role_security_users['operator_headers'])
    page = response.get_data(as_text=True)
    select_start = page.index(
        '<select id="{}"'.format(role_security_users['target_username']))
    select_end = page.index('</select>', select_start)
    target_role_menu = page[select_start:select_end]

    assert 'value="Administrator"' not in target_role_menu


def test_web_administrator_can_promote_user(
        app, client, role_security_users, basic_auth_admin_headers):
    response = post_web_role_change(
        client,
        basic_auth_admin_headers,
        role_security_users['target_username'],
        'Administrator',
    )

    assert response.status_code == 200
    assert_user_role(
        app, role_security_users['target_username'], 'Administrator')


def stored_setting(app, name):
    with app.app_context():
        row = Setting.query.filter_by(name=name).first()
        return None if row is None else row.value


def set_otp_secret(app, username, secret):
    with app.app_context():
        account = User.query.filter_by(username=username).one()
        account.otp_secret = secret
        account.otp_last_used = None
        db.session.commit()


def login_with_password(client, username, password):
    page = client.get('/login')
    token_match = re.search(
        rb'name="_csrf_token" value="([^"]+)"',
        page.data,
    )
    assert token_match is not None
    response = client.post(
        '/login',
        data={
            'username': username,
            'password': password,
            'auth_method': 'LOCAL',
            '_csrf_token': token_match.group(1).decode('utf-8'),
        },
    )
    assert response.status_code == 302
    return response


def test_web_operator_cannot_change_administrator_settings(
        app, client, role_security_users):
    headers = role_security_users['operator_headers']
    page = client.get('/admin/setting/basic', headers=headers)
    assert page.status_code == 200
    csrf_token, _ = csrf_token_for_manage_user(client, headers)
    before_url = stored_setting(app, 'pdns_api_url')
    before_key = stored_setting(app, 'pdns_api_key')

    edited = client.post(
        '/admin/setting/basic/pdns_api_url/edit',
        headers=headers,
        json={
            'value': 'http://127.0.0.1:9',
            '_csrf_token': csrf_token,
        },
    )
    toggled = client.post(
        '/admin/setting/basic/pdns_api_key/toggle',
        headers=headers,
        json={'_csrf_token': csrf_token},
    )
    unknown = client.post(
        '/admin/setting/basic/not_a_real_setting/edit',
        headers=headers,
        json={
            'value': 'x',
            '_csrf_token': csrf_token,
        },
    )

    assert edited.status_code == 403
    assert toggled.status_code == 403
    assert unknown.status_code == 403
    assert stored_setting(app, 'pdns_api_url') == before_url
    assert stored_setting(app, 'pdns_api_key') == before_key
    assert stored_setting(app, 'not_a_real_setting') is None
    assert b'pdns_api_url' not in page.data


def test_web_operator_can_still_edit_a_basic_setting(
        app, client, role_security_users):
    headers = role_security_users['operator_headers']
    csrf_token, _ = csrf_token_for_manage_user(client, headers)
    with app.app_context():
        original_name = Setting().get('site_name')
        original_gravatar = Setting().get('gravatar_enabled')
    try:
        renamed = client.post(
            '/admin/setting/basic/site_name/edit',
            headers=headers,
            json={
                'value': 'Operator Basic Site',
                '_csrf_token': csrf_token,
            },
        )
        assert renamed.status_code == 200
        with app.app_context():
            assert Setting().get('site_name') == 'Operator Basic Site'

        toggled = client.post(
            '/admin/setting/basic/gravatar_enabled/toggle',
            headers=headers,
            json={'_csrf_token': csrf_token},
        )
        assert toggled.status_code == 200
        with app.app_context():
            assert Setting().get('gravatar_enabled') is not original_gravatar
    finally:
        with app.app_context():
            Setting().set('site_name', original_name)
            Setting().set(
                'gravatar_enabled',
                'True' if original_gravatar else 'False')


def test_web_operator_cannot_disable_administrator_mfa(
        app, client, role_security_users, test_admin_user):
    secret = 'JBSWY3DPEHPK3PXP'
    set_otp_secret(app, test_admin_user, secret)
    try:
        login_with_password(
            client,
            role_security_users['operator_username'],
            role_security_users['operator_password'],
        )
        csrf_token, _ = csrf_token_for_manage_user(client, headers={})
        response = client.post(
            '/admin/manage-user',
            json={
                'action': 'user_otp_disable',
                'data': test_admin_user,
                '_csrf_token': csrf_token,
            },
        )
        assert response.status_code == 400
        assert 'Administrator' in response.get_json()['msg']
        with app.app_context():
            administrator = User.query.filter_by(
                username=test_admin_user).one()
            assert administrator.otp_secret == secret
    finally:
        set_otp_secret(app, test_admin_user, '')


def test_web_operator_cannot_remove_own_mfa_without_the_current_code(
        app, client, role_security_users):
    secret = 'JBSWY3DPEHPK3PXP'
    username = role_security_users['operator_username']
    login_with_password(
        client,
        username,
        role_security_users['operator_password'],
    )
    set_otp_secret(app, username, secret)
    try:
        csrf_token, _ = csrf_token_for_manage_user(client, headers={})
        refused = client.post(
            '/admin/manage-user',
            json={
                'action': 'user_otp_disable',
                'data': username,
                '_csrf_token': csrf_token,
            },
        )
        assert refused.status_code == 400
        assert 'current' in refused.get_json()['msg']
        with app.app_context():
            operator = User.query.filter_by(username=username).one()
            assert operator.otp_secret == secret

        disabled = client.post(
            '/admin/manage-user',
            json={
                'action': 'user_otp_disable',
                'data': username,
                'otp_token': pyotp.TOTP(secret).now(),
                '_csrf_token': csrf_token,
            },
        )
        assert disabled.status_code == 200
        with app.app_context():
            operator = User.query.filter_by(username=username).one()
            assert operator.otp_secret == ''
    finally:
        set_otp_secret(app, username, '')


def test_web_operator_can_disable_mfa_for_another_user(
        app, client, role_security_users):
    secret = 'JBSWY3DPEHPK3PXP'
    username = role_security_users['target_username']
    set_otp_secret(app, username, secret)
    try:
        csrf_token, _ = csrf_token_for_manage_user(
            client, role_security_users['operator_headers'])
        response = client.post(
            '/admin/manage-user',
            headers=role_security_users['operator_headers'],
            json={
                'action': 'user_otp_disable',
                'data': username,
                '_csrf_token': csrf_token,
            },
        )
        assert response.status_code == 200
        with app.app_context():
            target = User.query.filter_by(username=username).one()
            assert target.otp_secret == ''
    finally:
        set_otp_secret(app, username, '')


def test_web_operator_cannot_delete_an_administrator(
        app, client, role_security_users, test_admin_user):
    csrf_token, _ = csrf_token_for_manage_user(
        client, role_security_users['operator_headers'])
    response = client.post(
        '/admin/manage-user',
        headers=role_security_users['operator_headers'],
        json={
            'action': 'delete_user',
            'data': test_admin_user,
            '_csrf_token': csrf_token,
        },
    )

    assert response.status_code == 400
    assert 'Administrator' in response.get_json()['msg']
    with app.app_context():
        assert User.query.filter_by(username=test_admin_user).one()
