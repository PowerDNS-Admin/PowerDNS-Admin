import base64
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from flask import Flask, g
from werkzeug.exceptions import Forbidden, NotFound, Unauthorized

import powerdnsadmin.decorators as decorators
from powerdnsadmin.lib.errors import (DomainAccessForbidden,
                                      DomainOverrideForbidden,
                                      NotEnoughPrivileges,
                                      RecordTTLNotAllowed,
                                      RecordTypeNotAllowed,
                                      RequestIsNotJSON)


ALLOWED = object()


def user(role='User', user_id=7, username='alice', authenticated=True):
    return SimpleNamespace(
        id=user_id,
        username=username,
        role=SimpleNamespace(name=role),
        is_authenticated=authenticated,
    )


def apikey(role='User', key_id=11, domains=(), accounts=()):
    return SimpleNamespace(
        id=key_id,
        role=SimpleNamespace(name=role),
        domains=list(domains),
        accounts=list(accounts),
    )


class Settings:
    def __init__(self, **values):
        self.values = values

    def get(self, name):
        return self.values.get(name)

    def get_records_allow_to_edit(self):
        return self.values.get('record_types', [])

    def get_ttl_options(self):
        return self.values.get('ttl_options', [])


@pytest.fixture
def flask_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


def call(flask_app, wrapped, method='GET', json=None, headers=None,
         query_string=None, kwargs=None):
    with flask_app.test_request_context(
            '/', method=method, json=json, headers=headers,
            query_string=query_string):
        return wrapped(**(kwargs or {}))


@pytest.mark.parametrize(('decorator', 'allowed_roles'), [
    (decorators.admin_role_required, {'Administrator'}),
    (decorators.operator_role_required, {'Administrator', 'Operator'}),
])
@pytest.mark.parametrize('role', ['Administrator', 'Operator', 'User'])
def test_browser_role_decorators_enforce_their_role_contract(
        flask_app, monkeypatch, decorator, allowed_roles, role):
    monkeypatch.setattr(decorators, 'current_user', user(role))
    wrapped = decorator(lambda: ALLOWED)

    if role in allowed_roles:
        assert call(flask_app, wrapped) is ALLOWED
    else:
        with pytest.raises(Forbidden):
            call(flask_app, wrapped)


@pytest.mark.parametrize(
    ('decorator', 'setting_name', 'enabled_allows_user'), [
        (decorators.history_access_required, 'allow_user_view_history', True),
        (decorators.can_configure_dnssec, 'dnssec_admins_only', False),
        (decorators.can_remove_domain, 'allow_user_remove_domain', True),
        (decorators.can_create_domain, 'allow_user_create_domain', True),
    ])
def test_browser_setting_permissions_allow_and_reject_ordinary_users(
        flask_app, monkeypatch, decorator, setting_name, enabled_allows_user):
    monkeypatch.setattr(decorators, 'current_user', user())
    wrapped = decorator(lambda: ALLOWED)

    monkeypatch.setattr(
        decorators, 'Setting',
        lambda: Settings(**{setting_name: enabled_allows_user}))
    assert call(flask_app, wrapped) is ALLOWED

    monkeypatch.setattr(
        decorators, 'Setting',
        lambda: Settings(**{setting_name: not enabled_allows_user}))
    with pytest.raises(Forbidden):
        call(flask_app, wrapped)


@pytest.mark.parametrize('role', ['Administrator', 'Operator'])
def test_browser_setting_permissions_bypass_settings_for_privileged_roles(
        flask_app, monkeypatch, role):
    setting = MagicMock(side_effect=AssertionError('setting was consulted'))
    monkeypatch.setattr(decorators, 'current_user', user(role))
    monkeypatch.setattr(decorators, 'Setting', setting)

    for decorator in (
            decorators.history_access_required,
            decorators.can_configure_dnssec,
            decorators.can_remove_domain,
            decorators.can_create_domain):
        assert call(flask_app, decorator(lambda: ALLOWED)) is ALLOWED


def test_domain_access_checks_existence_and_user_grant(flask_app, monkeypatch):
    monkeypatch.setattr(decorators, 'current_user', user())
    domain_class = MagicMock()
    domain_class.name = MagicMock()
    monkeypatch.setattr(decorators, 'Domain', domain_class)
    wrapped = decorators.can_access_domain(lambda domain_name: ALLOWED)

    domain_class.query.filter.return_value.first.return_value = None
    with pytest.raises(NotFound):
        call(flask_app, wrapped, kwargs={'domain_name': 'missing.example'})

    stored_domain = SimpleNamespace(id=23)
    domain_class.query.filter.return_value.first.return_value = stored_domain
    domain_class.return_value.is_valid_access.return_value = False
    with pytest.raises(Forbidden):
        call(flask_app, wrapped, kwargs={'domain_name': 'private.example'})

    domain_class.return_value.is_valid_access.return_value = True
    assert call(flask_app, wrapped, kwargs={
        'domain_name': 'allowed.example'
    }) is ALLOWED
    domain_class.assert_called_with(id=23)
    domain_class.return_value.is_valid_access.assert_called_with(7)


def test_privileged_domain_access_does_not_query_database(flask_app,
                                                          monkeypatch):
    monkeypatch.setattr(decorators, 'current_user', user('Operator'))
    domain_class = MagicMock(
        side_effect=AssertionError('database was queried'))
    monkeypatch.setattr(decorators, 'Domain', domain_class)

    wrapped = decorators.can_access_domain(lambda domain_name: ALLOWED)

    assert call(
        flask_app, wrapped, kwargs={'domain_name': 'any.example'}) is ALLOWED


def test_api_authenticated_user_prefers_request_credentials(
        flask_app, monkeypatch):
    browser_user = user(username='browser')
    request_user = user(username='api')
    monkeypatch.setattr(decorators, 'current_user', browser_user)

    with flask_app.test_request_context('/'):
        assert decorators.api_authenticated_user() is browser_user
        g.basic_auth_user = request_user
        assert decorators.api_authenticated_user() is request_user


@pytest.mark.parametrize('method', ['POST', 'PUT', 'PATCH'])
def test_is_json_rejects_mutating_requests_without_json(flask_app, method):
    wrapped = decorators.is_json(lambda: ALLOWED)

    with pytest.raises(RequestIsNotJSON):
        call(flask_app, wrapped, method=method)
    assert call(flask_app, wrapped, method=method, json={}) is ALLOWED


def test_is_json_allows_read_requests_without_a_body(flask_app):
    assert call(flask_app, decorators.is_json(lambda: ALLOWED)) is ALLOWED


def test_body_key_callback_obeys_key_and_method_filters(flask_app):
    callback = MagicMock()
    wrapped = decorators.callback_if_request_body_contains_key(
        callback, http_methods=['PATCH'], keys=['dnssec'])(
            lambda zone_id: ALLOWED)

    assert call(
        flask_app, wrapped, method='PATCH', json={'dnssec': True},
        kwargs={'zone_id': 'example.'}) is ALLOWED
    callback.assert_called_once_with(zone_id='example.')

    callback.reset_mock()
    assert call(
        flask_app, wrapped, method='PATCH', json={'name': 'example.'},
        kwargs={'zone_id': 'example.'}) is ALLOWED
    assert call(
        flask_app, wrapped, method='POST', json={'dnssec': True},
        kwargs={'zone_id': 'example.'}) is ALLOWED
    callback.assert_not_called()


@pytest.mark.parametrize('identity_kwargs', [
    {'user_id': '7'},
    {'username': 'alice'},
])
def test_api_role_permission_allows_self(flask_app, monkeypatch,
                                         identity_kwargs):
    monkeypatch.setattr(decorators, 'current_user', user())
    wrapped = decorators.api_role_can(
        'read profile', roles=['Administrator'], allow_self=True)(
            lambda **kwargs: ALLOWED)

    assert call(flask_app, wrapped, kwargs=identity_kwargs) is ALLOWED


def test_api_role_permission_uses_basic_authenticated_user(
        flask_app, monkeypatch):
    monkeypatch.setattr(
        decorators, 'current_user', user('Administrator', username='browser'))
    wrapped = decorators.api_role_can('delete account')(
        lambda: ALLOWED)

    with flask_app.test_request_context('/'):
        g.basic_auth_user = user('User', username='api')
        with pytest.raises(NotEnoughPrivileges) as error:
            wrapped()

    assert 'User api with role User' in error.value.message
    assert 'delete account' in error.value.message


def test_api_role_permission_allows_default_privileged_roles(
        flask_app, monkeypatch):
    wrapped = decorators.api_role_can('list users')(lambda: ALLOWED)

    for role in ('Administrator', 'Operator'):
        monkeypatch.setattr(decorators, 'current_user', user(role))
        assert call(flask_app, wrapped) is ALLOWED


@pytest.mark.parametrize(
    ('decorator', 'setting_name'), [
        (decorators.api_can_create_domain, 'allow_user_create_domain'),
        (decorators.api_can_remove_domain, 'allow_user_remove_domain'),
    ])
def test_basic_user_zone_mutations_require_the_corresponding_setting(
        flask_app, monkeypatch, decorator, setting_name):
    monkeypatch.setattr(decorators, 'current_user', user())
    wrapped = decorator(lambda: ALLOWED)

    monkeypatch.setattr(
        decorators, 'Setting', lambda: Settings(**{setting_name: False}))
    with pytest.raises(NotEnoughPrivileges):
        call(flask_app, wrapped, method='POST', json={'name': 'example.'})

    monkeypatch.setattr(
        decorators, 'Setting', lambda: Settings(**{setting_name: True}))
    assert call(flask_app, wrapped, method='POST', json={
        'name': 'example.'
    }) is ALLOWED


def test_basic_zone_creation_rejects_domain_override(flask_app, monkeypatch):
    monkeypatch.setattr(decorators, 'current_user', user('Operator'))
    monkeypatch.setattr(
        decorators, 'Setting', lambda: Settings(deny_domain_override=True))
    domain_class = MagicMock()
    domain_class.return_value.is_overriding.return_value = True
    monkeypatch.setattr(decorators, 'Domain', domain_class)
    wrapped = decorators.api_can_create_domain(lambda: ALLOWED)

    with pytest.raises(DomainOverrideForbidden):
        call(flask_app, wrapped, method='POST', json={'name': 'example.'})

    domain_class.return_value.is_overriding.return_value = False
    assert call(flask_app, wrapped, method='POST', json={
        'name': 'example.'
    }) is ALLOWED


@pytest.mark.parametrize(
    ('decorator_factory', 'setting_name'), [
        (lambda f: decorators.apikey_can_create_domain(f),
         'allow_user_create_domain'),
        (lambda f: decorators.apikey_can_remove_domain()(f),
         'allow_user_remove_domain'),
    ])
def test_api_key_zone_mutations_require_the_corresponding_setting(
        flask_app, monkeypatch, decorator_factory, setting_name):
    wrapped = decorator_factory(lambda: ALLOWED)

    with flask_app.test_request_context('/', method='POST', json={
            'name': 'example.'}):
        g.apikey = apikey()
        monkeypatch.setattr(
            decorators, 'Setting', lambda: Settings(**{setting_name: False}))
        with pytest.raises(NotEnoughPrivileges):
            wrapped()

        monkeypatch.setattr(
            decorators, 'Setting', lambda: Settings(**{setting_name: True}))
        assert wrapped() is ALLOWED


def test_api_key_remove_permission_can_be_limited_by_method(
        flask_app, monkeypatch):
    monkeypatch.setattr(
        decorators, 'Setting',
        lambda: Settings(allow_user_remove_domain=False))
    wrapped = decorators.apikey_can_remove_domain(['DELETE'])(
        lambda: ALLOWED)

    with flask_app.test_request_context('/', method='GET'):
        g.apikey = apikey()
        assert wrapped() is ALLOWED

    with flask_app.test_request_context('/', method='DELETE'):
        g.apikey = apikey()
        with pytest.raises(NotEnoughPrivileges):
            wrapped()


def test_api_key_zone_creation_rejects_domain_override(
        flask_app, monkeypatch):
    monkeypatch.setattr(
        decorators, 'Setting', lambda: Settings(
            allow_user_create_domain=True, deny_domain_override=True))
    domain_class = MagicMock()
    domain_class.return_value.is_overriding.return_value = True
    monkeypatch.setattr(decorators, 'Domain', domain_class)
    wrapped = decorators.apikey_can_create_domain(lambda: ALLOWED)

    with flask_app.test_request_context(
            '/', method='POST', json={'name': 'example.'}):
        g.apikey = apikey()
        with pytest.raises(DomainOverrideForbidden):
            wrapped()

    with flask_app.test_request_context(
            '/', method='POST', json={'name': ''}):
        g.apikey = apikey()
        assert wrapped() is ALLOWED


def test_api_key_admin_permission(flask_app):
    wrapped = decorators.apikey_is_admin(lambda: ALLOWED)

    with flask_app.test_request_context('/'):
        g.apikey = apikey('Administrator')
        assert wrapped() is ALLOWED
        g.apikey = apikey('Operator')
        with pytest.raises(NotEnoughPrivileges):
            wrapped()


def test_api_key_domain_access_combines_direct_and_account_grants(flask_app):
    wrapped = decorators.apikey_can_access_domain(lambda zone_id: ALLOWED)
    direct = SimpleNamespace(name='direct.example')
    account_domain = SimpleNamespace(name='account.example')
    account = SimpleNamespace(domains=[account_domain])

    with flask_app.test_request_context('/'):
        g.apikey = apikey(domains=[direct], accounts=[account])
        assert wrapped(zone_id='direct.example.') is ALLOWED
        assert wrapped(zone_id='account.example.') is ALLOWED
        with pytest.raises(DomainAccessForbidden):
            wrapped(zone_id='forbidden.example.')

        g.apikey = apikey('Operator')
        assert wrapped(zone_id='any.example.') is ALLOWED


def test_api_key_dnssec_permission_honors_method_filter(
        flask_app, monkeypatch):
    monkeypatch.setattr(
        decorators, 'Setting', lambda: Settings(dnssec_admins_only=True))
    wrapped = decorators.apikey_can_configure_dnssec(['PATCH'])(
        lambda: ALLOWED)

    with flask_app.test_request_context('/', method='GET'):
        g.apikey = apikey()
        assert wrapped() is ALLOWED

    with flask_app.test_request_context('/', method='PATCH'):
        g.apikey = apikey()
        with pytest.raises(DomainAccessForbidden) as error:
            wrapped()
        assert 'configure dnssec' in error.value.message

        g.apikey = apikey('Operator')
        assert wrapped() is ALLOWED

    callback = decorators.apikey_can_configure_dnssec()()
    with flask_app.test_request_context('/', method='PATCH'):
        g.apikey = apikey('Operator')
        assert callback() is None


@pytest.mark.parametrize('method', ['GET', 'DELETE', 'PUT'])
def test_record_type_restriction_skips_read_and_replace_methods(
        flask_app, method):
    wrapped = decorators.allowed_record_types(lambda: ALLOWED)

    with flask_app.test_request_context('/', method=method):
        assert wrapped() is ALLOWED


def test_record_type_restriction_validates_every_rrset(flask_app,
                                                       monkeypatch):
    monkeypatch.setattr(
        decorators, 'Setting', lambda: Settings(record_types=['A', 'AAAA']))
    wrapped = decorators.allowed_record_types(lambda: ALLOWED)

    with flask_app.test_request_context(
            '/', method='PATCH', json={'rrsets': [{'type': 'A'}]}):
        g.apikey = apikey()
        assert wrapped() is ALLOWED

    with flask_app.test_request_context(
            '/', method='PATCH', json={'rrsets': [{'type': 'TXT'}]}):
        g.apikey = apikey()
        with pytest.raises(RecordTypeNotAllowed) as error:
            wrapped()
        assert error.value.message == 'Record type not allowed: TXT'

    with flask_app.test_request_context(
            '/', method='PATCH', json={'rrsets': [{}]}):
        g.apikey = apikey()
        with pytest.raises(RecordTypeNotAllowed):
            wrapped()


@pytest.mark.parametrize('payload, error_type', [({}, KeyError)])
def test_record_type_restriction_preserves_malformed_payload_errors(
        flask_app, monkeypatch, payload, error_type):
    monkeypatch.setattr(
        decorators, 'Setting', lambda: Settings(record_types=['A']))
    wrapped = decorators.allowed_record_types(lambda: ALLOWED)

    with flask_app.test_request_context('/', method='PATCH', json=payload):
        g.apikey = apikey()
        with pytest.raises(error_type):
            wrapped()


def test_record_type_restriction_rejects_json_null(flask_app, monkeypatch):
    monkeypatch.setattr(
        decorators, 'Setting', lambda: Settings(record_types=['A']))
    wrapped = decorators.allowed_record_types(lambda: ALLOWED)

    with flask_app.test_request_context(
            '/', method='PATCH', data='null', content_type='application/json'):
        g.apikey = apikey()
        with pytest.raises(TypeError):
            wrapped()


def test_record_type_restriction_bypasses_privileged_keys(flask_app):
    wrapped = decorators.allowed_record_types(lambda: ALLOWED)

    with flask_app.test_request_context('/', method='PATCH', json={}):
        g.apikey = apikey('Operator')
        assert wrapped() is ALLOWED


def test_record_ttl_restriction_validates_every_rrset(flask_app,
                                                      monkeypatch):
    monkeypatch.setattr(
        decorators, 'Setting', lambda: Settings(
            enforce_api_ttl=True, ttl_options=[(300, '5 minutes')]))
    wrapped = decorators.allowed_record_ttl(lambda: ALLOWED)

    with flask_app.test_request_context(
            '/', method='PATCH', json={'rrsets': [{'ttl': 300}]}):
        g.apikey = apikey()
        assert wrapped() is ALLOWED

    with flask_app.test_request_context(
            '/', method='PATCH', json={'rrsets': [{'ttl': 60}]}):
        g.apikey = apikey()
        with pytest.raises(RecordTTLNotAllowed) as error:
            wrapped()
        assert error.value.message == 'Record TTL not allowed: 60'

    with flask_app.test_request_context(
            '/', method='PATCH', json={'rrsets': [{}]}):
        g.apikey = apikey()
        with pytest.raises(RecordTTLNotAllowed):
            wrapped()


@pytest.mark.parametrize('payload, error_type', [({}, KeyError)])
def test_record_ttl_restriction_preserves_malformed_payload_errors(
        flask_app, monkeypatch, payload, error_type):
    monkeypatch.setattr(
        decorators, 'Setting', lambda: Settings(
            enforce_api_ttl=True, ttl_options=[(300, '5 minutes')]))
    wrapped = decorators.allowed_record_ttl(lambda: ALLOWED)

    with flask_app.test_request_context('/', method='PATCH', json=payload):
        g.apikey = apikey()
        with pytest.raises(error_type):
            wrapped()


def test_record_ttl_restriction_rejects_json_null(flask_app, monkeypatch):
    monkeypatch.setattr(
        decorators, 'Setting', lambda: Settings(
            enforce_api_ttl=True, ttl_options=[(300, '5 minutes')]))
    wrapped = decorators.allowed_record_ttl(lambda: ALLOWED)

    with flask_app.test_request_context(
            '/', method='PATCH', data='null', content_type='application/json'):
        g.apikey = apikey()
        with pytest.raises(TypeError):
            wrapped()


def test_record_ttl_restriction_bypass_contracts(flask_app, monkeypatch):
    wrapped = decorators.allowed_record_ttl(lambda: ALLOWED)

    monkeypatch.setattr(
        decorators, 'Setting', lambda: Settings(enforce_api_ttl=False))
    assert call(flask_app, wrapped, method='PATCH', json={}) is ALLOWED

    monkeypatch.setattr(
        decorators, 'Setting', lambda: Settings(enforce_api_ttl=True))
    with flask_app.test_request_context('/', method='GET'):
        assert wrapped() is ALLOWED
    with flask_app.test_request_context('/', method='PATCH', json={}):
        g.apikey = apikey('Administrator')
        assert wrapped() is ALLOWED


class FakeUser:
    validation_result = True
    validation_error = None
    email = None
    confirmed = True
    stored_user = user()
    query = MagicMock()
    username = MagicMock()
    instances = []

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.email = type(self).email
        self.confirmed = type(self).confirmed
        type(self).instances.append(self)

    def is_validate(self, method, src_ip):
        self.validation_method = method
        self.validation_ip = src_ip
        if type(self).validation_error:
            raise type(self).validation_error
        return type(self).validation_result


@pytest.fixture
def fake_user(monkeypatch):
    FakeUser.validation_result = True
    FakeUser.validation_error = None
    FakeUser.email = None
    FakeUser.confirmed = True
    FakeUser.stored_user = user()
    FakeUser.query = MagicMock()
    FakeUser.query.filter.return_value.first.return_value = (
        FakeUser.stored_user)
    FakeUser.instances = []
    monkeypatch.setattr(decorators, 'User', FakeUser)
    monkeypatch.setattr(
        decorators, 'Setting', lambda: Settings(verify_user_email=False))
    return FakeUser


def basic_header(value):
    encoded = base64.b64encode(value.encode()).decode()
    return {'Authorization': f'Basic {encoded}'}


def test_basic_auth_validates_credentials_and_sets_request_user(
        flask_app, monkeypatch, fake_user):
    monkeypatch.setattr(decorators, 'current_user', user(username='browser'))
    wrapped = decorators.api_basic_auth(decorators.api_authenticated_user)

    result = call(
        flask_app, wrapped, headers=basic_header('alice:secret'),
        query_string={'auth_method': 'LDAP'},
    )

    assert result is fake_user.stored_user
    candidate = fake_user.instances[0]
    assert candidate.username == 'alice'
    assert candidate.password == 'secret'
    assert candidate.plain_text_password == 'secret'
    assert candidate.validation_method == 'LDAP'
    fake_user.query.filter.return_value.first.assert_called_once()


@pytest.mark.parametrize('headers', [
    None,
    {'Authorization': 'Bearer token'},
    {'Authorization': 'Basic !!!'},
    basic_header('missing-colon'),
])
def test_basic_auth_rejects_missing_or_malformed_credentials(
        flask_app, fake_user, headers):
    wrapped = decorators.api_basic_auth(lambda: ALLOWED)

    with pytest.raises(Unauthorized):
        call(flask_app, wrapped, headers=headers)


def test_basic_auth_rejects_invalid_utf8_credentials(flask_app, fake_user):
    header = base64.b64encode(b'\xff\xfe').decode()
    wrapped = decorators.api_basic_auth(lambda: ALLOWED)

    with pytest.raises(Unauthorized):
        call(
            flask_app, wrapped,
            headers={'Authorization': f'Basic {header}'})


def test_basic_auth_rejects_unverified_or_invalid_users(
        flask_app, monkeypatch, fake_user):
    wrapped = decorators.api_basic_auth(lambda: ALLOWED)
    fake_user.email = 'alice@example.test'
    fake_user.confirmed = False
    monkeypatch.setattr(
        decorators, 'Setting', lambda: Settings(verify_user_email=True))

    with pytest.raises(Unauthorized):
        call(flask_app, wrapped, headers=basic_header('alice:secret'))

    fake_user.email = None
    fake_user.validation_result = False
    with pytest.raises(Unauthorized):
        call(flask_app, wrapped, headers=basic_header('alice:wrong'))

    fake_user.validation_result = True
    fake_user.validation_error = RuntimeError('backend unavailable')
    with pytest.raises(Unauthorized):
        call(flask_app, wrapped, headers=basic_header('alice:secret'))


class FakeApiKey:
    validation_result = apikey('Operator')
    validation_error = None
    instances = []

    def __init__(self, key):
        self.key = key
        type(self).instances.append(self)

    def is_validate(self, method, src_ip):
        self.validation_method = method
        self.validation_ip = src_ip
        if type(self).validation_error:
            raise type(self).validation_error
        return type(self).validation_result


@pytest.fixture
def fake_apikey(monkeypatch):
    FakeApiKey.validation_result = apikey('Operator')
    FakeApiKey.validation_error = None
    FakeApiKey.instances = []
    monkeypatch.setattr(decorators, 'ApiKey', FakeApiKey)
    return FakeApiKey


def api_key_header(value):
    return {'X-API-KEY': base64.b64encode(value.encode()).decode()}


def test_api_key_auth_validates_and_stores_key_on_request(
        flask_app, fake_apikey):
    wrapped = decorators.apikey_auth(lambda: g.apikey)

    result = call(flask_app, wrapped, headers=api_key_header('secret-key'))

    assert result is fake_apikey.validation_result
    candidate = fake_apikey.instances[0]
    assert candidate.key == 'secret-key'
    assert candidate.plain_text_password == 'secret-key'
    assert candidate.validation_method == 'LOCAL'


@pytest.mark.parametrize('headers', [
    None,
    {'X-API-KEY': 'a'},
    {'X-API-KEY': base64.b64encode(b'\xff\xfe').decode()},
])
def test_api_key_auth_rejects_missing_or_malformed_keys(
        flask_app, fake_apikey, headers):
    wrapped = decorators.apikey_auth(lambda: ALLOWED)

    with pytest.raises(Unauthorized):
        call(flask_app, wrapped, headers=headers)


def test_api_key_auth_rejects_validation_errors(flask_app, fake_apikey):
    fake_apikey.validation_error = RuntimeError('backend unavailable')
    wrapped = decorators.apikey_auth(lambda: ALLOWED)

    with pytest.raises(Unauthorized):
        call(flask_app, wrapped, headers=api_key_header('secret-key'))


@pytest.mark.parametrize('decorator', [
    decorators.api_basic_auth,
    decorators.apikey_auth,
])
def test_auth_decorators_reject_non_string_decoded_credentials(
        flask_app, monkeypatch, decorator):
    monkeypatch.setattr(
        decorators.base64, 'b64decode',
        MagicMock(side_effect=TypeError('credential must be bytes')))
    header_name = (
        'Authorization' if decorator is decorators.api_basic_auth
        else 'X-API-KEY')
    header_value = 'Basic encoded' if header_name == 'Authorization' else 'x'
    wrapped = decorator(lambda: ALLOWED)

    with pytest.raises(Unauthorized):
        call(flask_app, wrapped, headers={header_name: header_value})


def test_dynamic_dns_authentication_challenge(flask_app, monkeypatch):
    wrapped = decorators.dyndns_login_required(lambda: ALLOWED)
    monkeypatch.setattr(decorators, 'current_user', user(authenticated=False))

    response = call(flask_app, wrapped)

    assert response.status_code == 401
    assert response.headers['WWW-Authenticate'] == 'Basic'

    monkeypatch.setattr(decorators, 'current_user', user(authenticated=True))
    assert call(flask_app, wrapped) is ALLOWED


def test_combined_auth_dispatches_from_present_header(flask_app, monkeypatch):
    api_auth = MagicMock(return_value=lambda: 'api-key')
    basic_auth = MagicMock(return_value=lambda: 'basic')
    monkeypatch.setattr(decorators, 'apikey_auth', api_auth)
    monkeypatch.setattr(decorators, 'api_basic_auth', basic_auth)
    endpoint = lambda: ALLOWED
    wrapped = decorators.apikey_or_basic_auth(endpoint)

    assert call(
        flask_app, wrapped, headers={'X-API-KEY': 'present'}) == 'api-key'
    api_auth.assert_called_once_with(endpoint)
    basic_auth.assert_not_called()

    api_auth.reset_mock()
    assert call(flask_app, wrapped) == 'basic'
    basic_auth.assert_called_once_with(endpoint)
    api_auth.assert_not_called()
