import logging
from base64 import b64encode

import pytest

from powerdnsadmin.models import (
    Account,
    ApiKey,
    Domain,
    DomainUser,
    Role,
    Setting,
    User,
)
from powerdnsadmin.models.base import db


def basic_auth_headers(username, password):
    credentials = b64encode(
        '{}:{}'.format(username, password).encode('utf-8')
    ).decode('utf-8')
    return {'Authorization': 'Basic {}'.format(credentials)}


def apikey_headers(plain_key):
    encoded_key = b64encode(plain_key.encode('utf-8')).decode('utf-8')
    return {'X-API-KEY': encoded_key}


class ForwardResponse:
    def __init__(self, content=b'{}', status_code=200):
        self.content = content
        self.status_code = status_code
        self.headers = {}


@pytest.fixture
def api_security_data(app, initial_data):
    operator_username = 'api-security-operator'
    operator_password = 'OperatorPassword123!'
    allowed_domain_name = 'security-allowed.example'
    private_domain_name = 'security-private.example'

    with app.app_context():
        ordinary_user = User.query.filter_by(
            username=app.config['TEST_USER']).one()

        operator = User(
            username=operator_username,
            plain_text_password=operator_password,
            email='api-security-operator@example.com',
        )
        assert operator.create_local_user()['status']
        assert operator.set_role('Operator')['status']

        account = Account(
            name='security-private-account',
            description='Must not be disclosed',
            contact='Private Contact',
            mail='private-account@example.com',
        )
        allowed_domain = Domain(name=allowed_domain_name)
        private_domain = Domain(name=private_domain_name)
        private_domain.account = account
        db.session.add_all([account, allowed_domain, private_domain])
        db.session.flush()
        db.session.add(DomainUser(allowed_domain.id, ordinary_user.id))

        scoped_key = ApiKey(
            desc='ordinary-user-visible-key',
            role_name='User',
            domains=[allowed_domain],
        )
        scoped_plain_key = scoped_key.plain_key
        scoped_key.create()

        mixed_scope_key = ApiKey(
            desc='mixed-tenant-key',
            role_name='User',
            domains=[allowed_domain, private_domain],
            accounts=[account],
        )
        mixed_scope_plain_key = mixed_scope_key.plain_key
        mixed_scope_key.create()

        administrator_key = ApiKey(
            desc='security-administrator-key',
            role_name='Administrator',
        )
        administrator_plain_key = administrator_key.plain_key
        administrator_key.create()

        data = {
            'operator_headers': basic_auth_headers(
                operator_username, operator_password),
            'ordinary_headers': basic_auth_headers(
                app.config['TEST_USER'],
                app.config['TEST_USER_PASSWORD'],
            ),
            'scoped_key_headers': apikey_headers(scoped_plain_key),
            'administrator_key_headers': apikey_headers(
                administrator_plain_key),
            'scoped_key_id': scoped_key.id,
            'mixed_scope_key_id': mixed_scope_key.id,
            'mixed_scope_key_hash': mixed_scope_key.key,
            'allowed_domain_name': allowed_domain_name,
            'private_domain_name': private_domain_name,
            'private_account_name': account.name,
            'ordinary_user_id': ordinary_user.id,
            'operator_user_id': operator.id,
        }
        db.session.commit()

    yield data

    with app.app_context():
        for description in (
                'ordinary-user-visible-key',
                'mixed-tenant-key',
                'security-administrator-key',
                'allowed-operator-key'):
            key = ApiKey.query.filter_by(description=description).first()
            if key is not None:
                db.session.delete(key)

        allowed_domain = Domain.query.filter_by(
            name=allowed_domain_name).first()
        if allowed_domain is not None:
            DomainUser.query.filter_by(
                domain_id=allowed_domain.id).delete()
        for name in (allowed_domain_name, private_domain_name):
            domain = Domain.query.filter_by(name=name).first()
            if domain is not None:
                db.session.delete(domain)

        account = Account.query.filter_by(
            name=Account.sanitize_name('security-private-account')).first()
        if account is not None:
            db.session.delete(account)

        operator = User.query.filter_by(username=operator_username).first()
        if operator is not None:
            db.session.delete(operator)
        db.session.commit()


def test_basic_auth_ignores_administrator_session_for_user_credentials(
        app, client, api_security_data, test_admin_user):
    with app.app_context():
        administrator_id = User.query.filter_by(
            username=test_admin_user).one().id

    with client.session_transaction() as session:
        session['_user_id'] = str(administrator_id)
        session['_fresh'] = True

    response = client.get(
        '/api/v1/pdnsadmin/users',
        headers=api_security_data['ordinary_headers'],
    )

    assert response.status_code == 401


def test_basic_auth_uses_administrator_credentials_despite_user_session(
        client, api_security_data, basic_auth_admin_headers):
    with client.session_transaction() as session:
        session['_user_id'] = str(api_security_data['ordinary_user_id'])
        session['_fresh'] = True

    response = client.get(
        '/api/v1/pdnsadmin/users',
        headers=basic_auth_admin_headers,
    )

    assert response.status_code == 200


def test_self_user_response_has_an_explicit_safe_schema(
        client, api_security_data, test_user):
    response = client.get(
        '/api/v1/pdnsadmin/users/{}'.format(test_user),
        headers=api_security_data['ordinary_headers'],
    )

    assert response.status_code == 200
    assert set(response.get_json()) == {
        'id',
        'username',
        'firstname',
        'lastname',
        'email',
        'role',
        'accounts',
    }


def test_apikey_collection_never_returns_stored_verifiers(
        client, api_security_data, basic_auth_admin_headers):
    response = client.get(
        '/api/v1/pdnsadmin/apikeys',
        headers=basic_auth_admin_headers,
    )

    assert response.status_code == 200
    assert response.get_json()
    for key_data in response.get_json():
        assert set(key_data) == {
            'id', 'role', 'domains', 'accounts', 'description'
        }
        assert 'key' not in key_data
        assert 'plain_key' not in key_data


def test_apikey_detail_never_returns_stored_verifier(
        client, api_security_data, basic_auth_admin_headers):
    response = client.get(
        '/api/v1/pdnsadmin/apikeys/{}'.format(
            api_security_data['scoped_key_id']),
        headers=basic_auth_admin_headers,
    )

    assert response.status_code == 200
    assert set(response.get_json()) == {
        'id', 'role', 'domains', 'accounts', 'description'
    }


def test_apikey_collection_does_not_log_stored_verifiers(
        client, api_security_data, basic_auth_admin_headers, caplog):
    caplog.set_level(logging.DEBUG)

    response = client.get(
        '/api/v1/pdnsadmin/apikeys',
        headers=basic_auth_admin_headers,
    )

    assert response.status_code == 200
    assert api_security_data['mixed_scope_key_hash'] not in caplog.text


def test_user_apikey_collection_does_not_disclose_mixed_tenant_scope(
        client, api_security_data):
    response = client.get(
        '/api/v1/pdnsadmin/apikeys',
        headers=api_security_data['ordinary_headers'],
    )

    assert response.status_code == 200
    payload = response.get_json()
    serialized = str(payload)
    assert api_security_data['private_domain_name'] not in serialized
    assert api_security_data['private_account_name'] not in serialized
    assert api_security_data['mixed_scope_key_id'] not in {
        key_data['id'] for key_data in payload
    }
    assert api_security_data['scoped_key_id'] in {
        key_data['id'] for key_data in payload
    }


def test_user_cannot_get_mixed_tenant_apikey_by_id(
        client, api_security_data):
    response = client.get(
        '/api/v1/pdnsadmin/apikeys/{}'.format(
            api_security_data['mixed_scope_key_id']),
        headers=api_security_data['ordinary_headers'],
    )

    assert response.status_code == 403
    assert api_security_data['private_domain_name'] not in response.text
    assert api_security_data['private_account_name'] not in response.text


def test_unauthorized_apikey_lookup_does_not_reveal_id_existence(
        client, api_security_data):
    existing = client.get(
        '/api/v1/pdnsadmin/apikeys/{}'.format(
            api_security_data['mixed_scope_key_id']),
        headers=api_security_data['ordinary_headers'],
    )
    missing = client.get(
        '/api/v1/pdnsadmin/apikeys/2147483647',
        headers=api_security_data['ordinary_headers'],
    )

    assert existing.status_code == missing.status_code == 403
    assert existing.get_json() == missing.get_json()


@pytest.mark.parametrize('role_value', [
    pytest.param('Administrator', id='string-role'),
    pytest.param({'name': 'Administrator'}, id='object-role'),
])
def test_operator_cannot_create_administrator_apikey(
        app, client, api_security_data, role_value):
    response = client.post(
        '/api/v1/pdnsadmin/apikeys',
        headers=api_security_data['operator_headers'],
        json={
            'description': 'forbidden-operator-administrator-key',
            'role': role_value,
        },
    )

    assert response.status_code == 401
    with app.app_context():
        assert ApiKey.query.filter_by(
            description='forbidden-operator-administrator-key').first() is None


def test_operator_can_create_operator_apikey(
        app, client, api_security_data):
    response = client.post(
        '/api/v1/pdnsadmin/apikeys',
        headers=api_security_data['operator_headers'],
        json={
            'description': 'allowed-operator-key',
            'role': 'Operator',
        },
    )

    assert response.status_code == 201
    assert response.get_json()['role']['name'] == 'Operator'
    with app.app_context():
        assert ApiKey.query.filter_by(
            description='allowed-operator-key').one().role.name == 'Operator'


@pytest.mark.parametrize('role_value', [
    pytest.param('Administrator', id='string-role'),
    pytest.param({'name': 'Administrator'}, id='object-role'),
])
def test_operator_cannot_promote_apikey_to_administrator(
        app, client, api_security_data, role_value):
    with app.app_context():
        key = db.session.get(ApiKey, api_security_data['scoped_key_id'])
        key.role = Role.query.filter_by(name='User').one()
        db.session.commit()

    response = client.put(
        '/api/v1/pdnsadmin/apikeys/{}'.format(
            api_security_data['scoped_key_id']),
        headers=api_security_data['operator_headers'],
        json={'role': role_value},
    )

    assert response.status_code == 401
    with app.app_context():
        key = db.session.get(ApiKey, api_security_data['scoped_key_id'])
        assert key.role.name == 'User'


def test_user_cannot_delete_zone_when_remove_permission_is_disabled(
        app, client, api_security_data, monkeypatch):
    with app.app_context():
        assert Setting().set('allow_user_create_domain', True)
        assert Setting().set('allow_user_remove_domain', False)

    monkeypatch.setattr(
        'powerdnsadmin.routes.api.utils.fetch_remote',
        lambda *args, **kwargs: ForwardResponse(status_code=204),
    )
    monkeypatch.setattr(
        'powerdnsadmin.routes.api.Domain.update',
        lambda self: None,
    )

    response = client.delete(
        '/api/v1/pdnsadmin/zones/{}'.format(
            api_security_data['allowed_domain_name']),
        headers=api_security_data['ordinary_headers'],
    )

    assert response.status_code == 401

    with app.app_context():
        assert Setting().set('allow_user_remove_domain', True)


def test_user_cannot_trigger_domain_synchronization(
        client, api_security_data, monkeypatch):
    monkeypatch.setattr(
        'powerdnsadmin.routes.api.Domain.update',
        lambda self: pytest.fail('domain synchronization must not run'),
    )

    response = client.get(
        '/api/v1/sync_domains',
        headers=api_security_data['ordinary_headers'],
    )

    assert response.status_code == 401


def test_user_apikey_cannot_trigger_domain_synchronization(
        client, api_security_data, monkeypatch):
    monkeypatch.setattr(
        'powerdnsadmin.routes.api.Domain.update',
        lambda self: pytest.fail('domain synchronization must not run'),
    )

    response = client.get(
        '/api/v1/sync_domains',
        headers=api_security_data['scoped_key_headers'],
    )

    assert response.status_code == 401


def test_operator_can_trigger_domain_synchronization(
        client, api_security_data, monkeypatch):
    synchronized = []
    monkeypatch.setattr(
        'powerdnsadmin.routes.api.Domain.update',
        lambda self: synchronized.append(True),
    )

    response = client.get(
        '/api/v1/sync_domains',
        headers=api_security_data['operator_headers'],
    )

    assert response.status_code == 200
    assert synchronized == [True]


@pytest.mark.parametrize('path', [
    pytest.param('/api/v1/servers', id='server-list'),
    pytest.param('/api/v1/servers/localhost', id='server-detail'),
])
def test_user_apikey_cannot_read_server_metadata(
        path,
        client, api_security_data, monkeypatch):
    monkeypatch.setattr(
        'powerdnsadmin.routes.api.helper.forward_request',
        lambda: pytest.fail('server metadata must not be forwarded'),
    )

    response = client.get(
        path,
        headers=api_security_data['scoped_key_headers'],
    )

    assert response.status_code == 401


def test_administrator_apikey_can_read_server_metadata(
        client, api_security_data, monkeypatch):
    monkeypatch.setattr(
        'powerdnsadmin.routes.api.helper.forward_request',
        lambda: ForwardResponse(content=b'{"id":"localhost"}'),
    )

    response = client.get(
        '/api/v1/servers/localhost',
        headers=api_security_data['administrator_key_headers'],
    )

    assert response.status_code == 200
    assert response.get_data(as_text=True) == '{"id":"localhost"}'


def test_user_apikey_cannot_access_another_tenants_zone_subpath(
        client, api_security_data, monkeypatch):
    monkeypatch.setattr(
        'powerdnsadmin.routes.api.helper.forward_request',
        lambda: pytest.fail('unauthorized zone request must not be forwarded'),
    )

    response = client.get(
        '/api/v1/servers/localhost/zones/{}/metadata'.format(
            api_security_data['private_domain_name']),
        headers=api_security_data['scoped_key_headers'],
    )

    assert response.status_code == 403


def test_user_apikey_can_access_its_own_zone_subpath(
        client, api_security_data, monkeypatch):
    monkeypatch.setattr(
        'powerdnsadmin.routes.api.helper.forward_request',
        lambda: ForwardResponse(content=b'[]'),
    )

    response = client.get(
        '/api/v1/servers/localhost/zones/{}/metadata'.format(
            api_security_data['allowed_domain_name']),
        headers=api_security_data['scoped_key_headers'],
    )

    assert response.status_code == 200
    assert response.get_data(as_text=True) == '[]'
