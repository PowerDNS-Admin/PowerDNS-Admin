import json
import re
from base64 import b64encode
from datetime import datetime

from powerdnsadmin.lib.api_audit import (
    redact_for_audit,
    redact_query_string,
    serialize_request_body,
    serialize_response_text,
    should_audit_path,
)
from powerdnsadmin.models.api_history import ApiHistory
from powerdnsadmin.models.api_key import ApiKey
from powerdnsadmin.models.base import db
from powerdnsadmin.models.user import User


def test_every_api_path_is_audited():
    assert should_audit_path('/api')
    assert should_audit_path('/api/v1/pdnsadmin/users')
    assert should_audit_path('/api/v1/servers/pdnsadmin/zones')
    assert should_audit_path('/api/v1/servers')
    assert should_audit_path('/api/v1/servers/localhost')
    assert should_audit_path('/api/v1/servers/localhost/')
    assert should_audit_path('/api/v1/servers/localhost/zones/example.org.')
    assert not should_audit_path('/login')
    assert not should_audit_path('/ping')
    assert not should_audit_path('/apikeys')


def test_redact_for_audit_replaces_nested_credentials_without_mutating_input():
    payload = {
        'username': 'audit-target',
        'plain_text_password': 'SecretPassword123!',
        'otp_secret': 'JBSWY3DPEHPK3PXP',
        'profile': {'password': 'nested-secret', 'email': 'a@example.com'},
    }

    redacted = redact_for_audit(payload)

    assert redacted['username'] == 'audit-target'
    assert redacted['plain_text_password'] == '[redacted]'
    assert redacted['otp_secret'] == '[redacted]'
    assert redacted['profile']['password'] == '[redacted]'
    assert redacted['profile']['email'] == 'a@example.com'
    assert payload['plain_text_password'] == 'SecretPassword123!'


def test_query_string_credentials_are_redacted():
    redacted = redact_query_string(
        'auth_method=LOCAL&plain_text_password=QuerySecret')

    assert 'auth_method=LOCAL' in redacted
    assert 'QuerySecret' not in redacted
    assert 'plain_text_password=%5Bredacted%5D' in redacted


def test_oversized_request_body_is_omitted_after_redaction():
    payload = {
        'plain_text_password': 'SecretPassword123!',
        'comment': 'x' * 40000,
    }

    stored = serialize_request_body(payload)

    assert stored == '{"_omitted":"request body exceeded audit size limit"}'
    assert 'SecretPassword123!' not in stored


def test_response_text_redacts_secrets_and_omits_oversized_payloads():
    stored = serialize_response_text(
        '{"plain_key":"supersecret","name":"yinzcloud.net."}')

    assert json.loads(stored) == {
        'plain_key': '[redacted]',
        'name': 'yinzcloud.net.',
    }
    assert 'supersecret' not in stored
    assert serialize_response_text('') is None
    assert serialize_response_text(None) is None

    oversized = serialize_response_text(json.dumps({'rrsets': ['x' * 40000]}))

    assert oversized == '{"_omitted":"response body exceeded audit size limit"}'
    assert 'xxxx' not in oversized


def _rows(app, **filters):
    with app.app_context():
        db.session.remove()
        found = (
            ApiHistory.query.filter_by(**filters)
            .order_by(ApiHistory.id.asc())
            .all()
        )
        copied = [
            {
                'method': row.method,
                'path': row.path,
                'query_string': row.query_string,
                'status_code': row.status_code,
                'auth_type': row.auth_type,
                'authenticated': bool(row.authenticated),
                'user_id': row.user_id,
                'username': row.username,
                'apikey_id': row.apikey_id,
                'apikey_description': row.apikey_description,
                'request_body': row.request_body,
                'response_body': row.response_body,
            }
            for row in found
        ]
        return copied


def _combined(row):
    return '\n'.join(
        str(value) for value in row.values() if value is not None)


def _version_list_key(app):
    with app.app_context():
        api_key = ApiKey(desc='version list', role_name='User', domains=[])
        plain_key = api_key.plain_key
        api_key.create()
        key_id = api_key.id
    header = b64encode(plain_key.encode('utf-8')).decode('utf-8')
    return {'X-API-KEY': header}, key_id


def test_version_list_requires_a_valid_api_key(app, initial_data, client):
    missing = client.get('/api')
    assert missing.status_code == 401
    assert missing.get_json() == {'msg': 'Unauthorized'}

    encoded_key = b64encode(b'not-a-real-api-key').decode('utf-8')
    rejected = client.get('/api', headers={'X-API-KEY': encoded_key})
    assert rejected.status_code == 401
    assert rejected.get_json() == {'msg': 'Unauthorized'}

    headers, key_id = _version_list_key(app)
    accepted = client.get('/api', headers=headers)
    assert accepted.status_code == 200
    assert json.loads(accepted.get_data(as_text=True)) == [
        {'url': '/api/v1', 'version': 1}]

    rows = _rows(app, path='/api', method='GET')
    assert rows[-3]['status_code'] == 401
    assert rows[-3]['auth_type'] == 'none'
    assert rows[-3]['authenticated'] is False
    assert json.loads(rows[-3]['response_body']) == {'msg': 'Unauthorized'}
    assert rows[-2]['status_code'] == 401
    assert rows[-2]['auth_type'] == 'api_key'
    assert rows[-2]['authenticated'] is False
    assert rows[-2]['apikey_id'] is None
    assert 'not-a-real-api-key' not in _combined(rows[-2])
    accepted_row = rows[-1]
    assert accepted_row['status_code'] == 200
    assert accepted_row['auth_type'] == 'api_key'
    assert accepted_row['authenticated'] is True
    assert accepted_row['apikey_id'] == key_id
    assert accepted_row['apikey_description'] == 'version list'
    assert accepted_row['request_body'] is None
    assert json.loads(accepted_row['response_body']) == [
        {'url': '/api/v1', 'version': 1}]


def test_version_list_and_authenticated_read_are_audited(
        app, initial_data, client, basic_auth_admin_headers):
    headers, key_id = _version_list_key(app)
    version = client.get('/api', headers=headers)
    assert version.status_code == 200

    users = client.get(
        '/api/v1/pdnsadmin/users?auth_method=LOCAL&plain_text_password=QuerySecret',
        headers=basic_auth_admin_headers,
    )
    assert users.status_code == 200

    version_rows = _rows(app, path='/api', method='GET')
    assert version_rows[-1]['status_code'] == 200
    assert version_rows[-1]['auth_type'] == 'api_key'
    assert version_rows[-1]['authenticated'] is True
    assert version_rows[-1]['apikey_id'] == key_id
    assert version_rows[-1]['request_body'] is None

    with app.app_context():
        admin = User.query.filter_by(username=app.config['TEST_ADMIN_USER']).one()
        admin_id = admin.id

    user_rows = _rows(app, path='/api/v1/pdnsadmin/users', method='GET')
    recorded = user_rows[-1]
    assert recorded['status_code'] == 200
    assert recorded['auth_type'] == 'basic'
    assert recorded['authenticated'] is True
    assert recorded['user_id'] == admin_id
    assert recorded['username'] == app.config['TEST_ADMIN_USER']
    assert 'QuerySecret' not in _combined(recorded)
    assert 'plain_text_password=%5Bredacted%5D' in recorded['query_string']


def test_failed_credentials_are_audited_without_the_secret(
        app, initial_data, client):
    basic = b64encode(b'admin:wrong-password').decode('utf-8')
    rejected_basic = client.get(
        '/api/v1/pdnsadmin/users',
        headers={'Authorization': 'Basic {}'.format(basic)},
    )
    assert rejected_basic.status_code == 401

    plain_key = 'not-a-real-api-key'
    encoded_key = b64encode(plain_key.encode('utf-8')).decode('utf-8')
    rejected_key = client.get(
        '/api/v1/pdnsadmin/accounts',
        headers={'X-API-KEY': encoded_key},
    )
    assert rejected_key.status_code == 401

    basic_rows = _rows(app, path='/api/v1/pdnsadmin/users', method='GET')
    basic_row = basic_rows[-1]
    assert basic_row['status_code'] == 401
    assert basic_row['auth_type'] == 'basic'
    assert basic_row['authenticated'] is False
    assert basic_row['username'] == 'admin'
    assert basic_row['user_id'] is None
    assert 'wrong-password' not in _combined(basic_row)
    assert basic not in _combined(basic_row)

    key_rows = _rows(app, path='/api/v1/pdnsadmin/accounts', method='GET')
    key_row = key_rows[-1]
    assert key_row['status_code'] == 401
    assert key_row['auth_type'] == 'api_key'
    assert key_row['authenticated'] is False
    assert key_row['apikey_id'] is None
    assert plain_key not in _combined(key_row)
    assert encoded_key not in _combined(key_row)


def test_create_user_body_is_stored_with_secrets_removed(
        app, initial_data, client, basic_auth_admin_headers):
    password = 'SecretPassword123!'
    otp_secret = 'JBSWY3DPEHPK3PXP'
    response = client.post(
        '/api/v1/pdnsadmin/users',
        headers=basic_auth_admin_headers,
        json={
            'username': 'audit-target',
            'email': 'audit-target@example.com',
            'plain_text_password': password,
            'otp_secret': otp_secret,
            'confirmed': True,
        },
    )
    assert response.status_code == 201

    recorded = _rows(app, path='/api/v1/pdnsadmin/users', method='POST')[-1]
    body = json.loads(recorded['request_body'])
    assert recorded['status_code'] == 201
    assert recorded['authenticated'] is True
    assert recorded['username'] == app.config['TEST_ADMIN_USER']
    assert body['username'] == 'audit-target'
    assert body['plain_text_password'] == '[redacted]'
    assert body['otp_secret'] == '[redacted]'
    assert password not in recorded['request_body']
    assert otp_secret not in recorded['request_body']
    returned = json.loads(recorded['response_body'])
    assert returned['username'] == 'audit-target'
    assert returned['email'] == 'audit-target@example.com'
    assert password not in recorded['response_body']
    assert otp_secret not in recorded['response_body']


def test_localhost_passthrough_is_audited_with_other_api_calls(
        app, initial_data, client, monkeypatch):
    class ForwardResponse:
        content = b'[]'
        status_code = 200
        headers = {}

    monkeypatch.setattr(
        'powerdnsadmin.routes.api.helper.forward_request',
        lambda: ForwardResponse(),
    )

    with app.app_context():
        key = ApiKey(desc='audit-admin-key', role_name='Administrator')
        plain_key = key.plain_key
        key.create()
        key_id = key.id

    headers = {
        'X-API-KEY': b64encode(plain_key.encode('utf-8')).decode('utf-8'),
    }

    passthrough = client.get(
        '/api/v1/servers/localhost/zones', headers=headers)
    assert passthrough.status_code == 200
    proxied = _rows(app, path='/api/v1/servers/localhost/zones', method='GET')[-1]
    assert proxied['status_code'] == 200
    assert proxied['auth_type'] == 'api_key'
    assert proxied['apikey_id'] == key_id
    assert proxied['apikey_description'] == 'audit-admin-key'
    assert proxied['response_body'] == '[]'
    assert plain_key not in _combined(proxied)

    server_list = client.get('/api/v1/servers', headers=headers)
    assert server_list.status_code == 200
    server_row = _rows(app, path='/api/v1/servers', method='GET')[-1]
    assert server_row['status_code'] == 200
    assert server_row['auth_type'] == 'api_key'
    assert server_row['apikey_id'] == key_id
    assert server_row['apikey_description'] == 'audit-admin-key'
    assert plain_key not in _combined(server_row)

    local_zones = client.get(
        '/api/v1/servers/pdnsadmin/zones', headers=headers)
    assert local_zones.status_code == 200
    zone_row = _rows(
        app, path='/api/v1/servers/pdnsadmin/zones', method='GET')[-1]
    assert zone_row['authenticated'] is True
    assert zone_row['apikey_id'] == key_id


def _csrf_token(response):
    match = re.search(
        rb'name="_csrf_token" value="([^"]+)"',
        response.data,
    )
    assert match is not None
    return match.group(1).decode('utf-8')


def _login(client, username, password):
    page = client.get('/login')
    response = client.post(
        '/login',
        data={
            'username': username,
            'password': password,
            'auth_method': 'LOCAL',
            '_csrf_token': _csrf_token(page),
        },
    )
    assert response.status_code == 302
    return response


def _add_api_history(app, **overrides):
    values = {
        'created_on': datetime.utcnow(),
        'method': 'POST',
        'path': '/api/v1/pdnsadmin/users',
        'query_string': 'auth_method=LOCAL',
        'status_code': 201,
        'remote_addr': '203.0.113.10',
        'auth_type': 'basic',
        'authenticated': True,
        'user_id': 1,
        'username': 'admin',
        'request_body': (
            '{"username":"audit-target",'
            '"plain_text_password":"[redacted]",'
            '"note":"<script>alert(1)</script>"}'
        ),
        'response_body': '{"username":"audit-target","id":9}',
    }
    values.update(overrides)
    with app.app_context():
        row = ApiHistory(**values)
        db.session.add(row)
        db.session.commit()
        row_id = row.id
        db.session.remove()
        return row_id


def test_api_history_page_lists_recorded_calls_for_an_administrator(
        app, initial_data, client):
    marker = '/api/v1/pdnsadmin/users/audit-page-marker'
    other = '/api/v1/pdnsadmin/accounts/audit-page-other'
    _add_api_history(app, path=marker, username='audit-admin')
    _add_api_history(
        app,
        method='GET',
        path=other,
        status_code=401,
        auth_type='api_key',
        authenticated=False,
        user_id=None,
        username=None,
        apikey_id=44,
        apikey_description='audit-reader',
        query_string=None,
        request_body=None,
        remote_addr='198.51.100.4',
    )
    _login(client, app.config['TEST_ADMIN_USER'], app.config['TEST_ADMIN_PASSWORD'])

    page = client.get('/admin/api-history')
    body = page.get_data(as_text=True)

    assert page.status_code == 200
    assert 'API History' in body
    assert 'href="/admin/api-history"' in body
    assert marker in body
    assert 'audit-admin' in body
    assert '203.0.113.10' in body
    assert '[redacted]' in body
    assert 'Response body' in body
    assert 'api-history-response' in body
    assert '&#34;id&#34;: 9' in body
    assert '<script>alert(1)</script>' not in body
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in body

    filtered = client.get('/admin/api-history?path=audit-page-marker')
    filtered_body = filtered.get_data(as_text=True)
    assert filtered.status_code == 200
    assert marker in filtered_body
    assert other not in filtered_body

    by_key = client.get('/admin/api-history?actor=audit-reader&outcome=unauthenticated')
    key_body = by_key.get_data(as_text=True)
    assert other in key_body
    assert 'audit-reader' in key_body
    assert marker not in key_body


def test_api_history_page_is_closed_to_ordinary_users(
        app, initial_data, client):
    _login(client, app.config['TEST_USER'], app.config['TEST_USER_PASSWORD'])

    response = client.get('/admin/api-history')

    assert response.status_code == 403


def test_api_history_records_host_and_user_agent(app, initial_data, client):
    response = client.get(
        '/api/v1/audit-client-marker',
        base_url='http://dns.example:9191',
        headers={'User-Agent': 'audit-client/9'},
    )
    assert response.status_code == 404
    recorded = _rows(app, path='/api/v1/audit-client-marker')[-1]
    with app.app_context():
        row = ApiHistory.query.filter_by(
            path='/api/v1/audit-client-marker').one()
        assert row.host == 'dns.example:9191'
        assert row.user_agent == 'audit-client/9'
    assert recorded['path'] == '/api/v1/audit-client-marker'


def test_unknown_api_path_is_audited_and_other_routes_are_not(
        app, initial_data, client):
    missing = client.get('/api/v1/audit-probe-does-not-exist')
    assert missing.status_code == 404
    recorded = _rows(
        app, path='/api/v1/audit-probe-does-not-exist', method='GET')[-1]
    assert recorded['status_code'] == 404
    assert recorded['auth_type'] == 'none'

    ping = client.get('/ping')
    assert ping.status_code == 200
    assert _rows(app, path='/ping') == []
