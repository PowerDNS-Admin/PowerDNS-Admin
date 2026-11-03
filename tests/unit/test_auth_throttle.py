import logging
from base64 import b64encode
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Barrier, Lock

import pytest

from powerdnsadmin.lib.auth_throttle import (
    acquire_inflight, assert_throttle_store, record_password_failure,
    release_inflight)
from powerdnsadmin.models.api_key import ApiKey
from powerdnsadmin.models.auth_attempt import AuthAttempt
from powerdnsadmin.models.base import db
from powerdnsadmin.models.user import User


_LIMITS = {
    'AUTH_SOURCE_LIMIT': 3,
    'AUTH_ACCOUNT_LIMIT': 3,
    'AUTH_PAIR_LIMIT': 3,
    'AUTH_MAX_IN_FLIGHT': 32,
    'AUTH_SPRAY_USERNAMES': 3,
    'AUTH_SPRAY_SOURCES': 3,
    'AUTH_TRUSTED_PROXIES': [],
}


@pytest.fixture
def tight_limits(app, initial_data):
    previous = {key: app.config.get(key) for key in _LIMITS}
    app.config.update(_LIMITS)
    with app.app_context():
        AuthAttempt.query.delete()
        db.session.commit()
    yield
    app.config.update(previous)
    with app.app_context():
        AuthAttempt.query.delete()
        db.session.commit()


def _csrf(response):
    import re
    match = re.search(rb'name="_csrf_token" value="([^"]+)"', response.data)
    assert match is not None
    return match.group(1).decode('utf-8')


def _login(client, username, password, ip, forwarded=None):
    page = client.get('/login', environ_base={'REMOTE_ADDR': ip})
    headers = {}
    if forwarded is not None:
        headers['X-Forwarded-For'] = forwarded
    return client.post(
        '/login',
        data={
            'username': username,
            'password': password,
            'auth_method': 'LOCAL',
            '_csrf_token': _csrf(page),
        },
        headers=headers,
        environ_base={'REMOTE_ADDR': ip},
    )


def _lease_token(lease):
    return lease[0]


def _basic(username, password):
    token = b64encode('{0}:{1}'.format(username, password).encode('utf-8'))
    return {'Authorization': 'Basic {0}'.format(token.decode('utf-8'))}


def test_rotating_usernames_share_one_source_budget(
        app, client, tight_limits, monkeypatch):
    calls = {'n': 0}

    def reject_password(self, hashed):
        calls['n'] += 1
        return False

    monkeypatch.setattr(User, 'check_password', reject_password)
    ip = '198.51.100.10'
    for name in ('spray-a', 'spray-b'):
        response = _login(client, name, 'wrong-password', ip)
        assert response.status_code == 200
        assert b'Invalid credentials' in response.data
        assert b'does not exist' not in response.data.lower()
    assert _login(client, 'spray-c', 'wrong-password', ip).status_code == 429
    blocked = _login(
        client, app.config['TEST_USER'], 'wrong-password', ip)
    assert blocked.status_code == 429
    assert blocked.headers['Retry-After']
    assert b'Too many authentication attempts' in blocked.data
    assert calls['n'] == 0


def test_rotating_addresses_share_one_account_budget(
        app, client, tight_limits, monkeypatch):
    calls = {'n': 0}

    def reject_password(self, hashed):
        calls['n'] += 1
        return False

    monkeypatch.setattr(User, 'check_password', reject_password)
    username = app.config['TEST_USER']
    for last in (1, 2):
        response = _login(
            client, username, 'wrong-password', '198.51.100.{0}'.format(last))
        assert response.status_code == 200
    assert _login(
        client, username, 'wrong-password', '198.51.100.3').status_code == 429
    blocked = _login(client, username, 'wrong-password', '198.51.100.4')
    assert blocked.status_code == 429
    other = _login(client, 'someone-else', 'wrong-password', '198.51.100.5')
    assert other.status_code == 200
    assert calls['n'] == 3


def test_login_basic_and_dyndns_share_the_same_budget(
        app, client, tight_limits):
    username = app.config['TEST_USER']
    ip = '198.51.100.40'
    first = _login(client, username, 'wrong-password', ip)
    assert first.status_code == 200
    second = client.get(
        '/api/v1/pdnsadmin/users',
        headers=_basic(username, 'wrong-password'),
        environ_base={'REMOTE_ADDR': ip},
    )
    assert second.status_code == 401
    assert second.get_json()['msg'] == 'Unauthorized'
    third = client.get(
        '/nic/update',
        headers=_basic(username, 'wrong-password'),
        environ_base={'REMOTE_ADDR': ip},
    )
    assert third.status_code == 429
    assert third.headers['Retry-After']
    assert b'does not exist' not in third.data.lower()


def test_unknown_user_and_bad_password_look_the_same(
        app, client, tight_limits):
    ip = '198.51.100.60'
    unknown = client.get(
        '/api/v1/pdnsadmin/users',
        headers=_basic('missing-person', 'wrong-password'),
        environ_base={'REMOTE_ADDR': ip},
    )
    wrong = client.get(
        '/api/v1/pdnsadmin/users',
        headers=_basic(app.config['TEST_USER'], 'wrong-password'),
        environ_base={'REMOTE_ADDR': '198.51.100.61'},
    )
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.get_json() == wrong.get_json()


def test_spoofed_forwarded_header_does_not_reset_the_budget(
        app, client, tight_limits):
    ip = '198.51.100.70'
    assert _login(client, 'header-spray', 'wrong-password', ip).status_code == 200
    assert _login(client, 'header-spray', 'wrong-password', ip).status_code == 200
    assert _login(client, 'header-spray', 'wrong-password', ip).status_code == 429
    spoofed = _login(
        client, 'header-spray-2', 'wrong-password', ip,
        forwarded='203.0.113.50')
    assert spoofed.status_code == 429

    app.config['AUTH_TRUSTED_PROXIES'] = [ip]
    fresh = _login(
        client, 'header-spray-3', 'wrong-password', ip,
        forwarded='203.0.113.51')
    assert fresh.status_code == 200
    assert b'Invalid credentials' in fresh.data


def test_success_keeps_failures_against_other_accounts(
        app, client, tight_limits):
    ip = '198.51.100.80'
    username = app.config['TEST_USER']
    password = app.config['TEST_USER_PASSWORD']
    assert _login(client, username, 'wrong-password', ip).status_code == 200
    assert _login(client, username, 'wrong-password', ip).status_code == 200
    signed_in = _login(client, username, password, ip)
    assert signed_in.status_code == 302
    client.get('/logout', environ_base={'REMOTE_ADDR': ip})
    blocked = _login(client, 'other-account', 'wrong-password', ip)
    assert blocked.status_code == 429
    elsewhere = _login(
        client, username, 'wrong-password', '198.51.100.81')
    assert elsewhere.status_code == 200


def test_concurrency_limit_skips_the_password_check(
        app, client, tight_limits, monkeypatch):
    calls = {'n': 0}

    def reject_password(self, hashed):
        calls['n'] += 1
        return False

    monkeypatch.setattr(User, 'check_password', reject_password)
    app.config['AUTH_MAX_IN_FLIGHT'] = 1
    with app.app_context():
        lease = acquire_inflight()
        assert lease
        lease = _lease_token(lease)
    try:
        response = _login(
            client, app.config['TEST_USER'], 'wrong-password',
            '198.51.100.90')
        assert response.status_code == 429
        assert calls['n'] == 0
    finally:
        with app.app_context():
            release_inflight(lease)


def test_malformed_basic_credentials_spend_the_source_budget(
        app, client, tight_limits):
    ip = '198.51.100.100'
    for _ in range(2):
        response = client.get(
            '/api/v1/pdnsadmin/users',
            headers={'Authorization': 'Basic not-valid'},
            environ_base={'REMOTE_ADDR': ip},
        )
        assert response.status_code == 401
    blocked = client.get(
        '/api/v1/pdnsadmin/users',
        headers=_basic(app.config['TEST_USER'], 'wrong-password'),
        environ_base={'REMOTE_ADDR': ip},
    )
    assert blocked.status_code == 429


def test_spray_is_logged_without_the_password(
        app, client, tight_limits, caplog):
    caplog.set_level(logging.WARNING)
    secret = 'UniqueSpraySecret-not-a-username'
    ip = '198.51.100.110'
    for name in ('logged-a', 'logged-b', 'logged-c'):
        _login(client, name, secret, ip)
    assert 'distinct usernames' in caplog.text
    assert secret not in caplog.text


def test_workers_share_one_database_counter(app, tight_limits):
    barrier = Barrier(8)
    source = '198.51.100.120'

    def fail_once(_slot):
        with app.app_context():
            try:
                barrier.wait(timeout=10)
                record_password_failure(source, 'shared-account')
            finally:
                db.session.remove()

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(fail_once, range(8)))

    with app.app_context():
        row = AuthAttempt.query.filter_by(scope='source', subject=source).one()
        assert row.failures == 3
        assert row.locked_until is not None
        account = AuthAttempt.query.filter_by(
            scope='account', subject='shared-account').one()
        assert account.failures == 3


def test_inflight_leases_expire_on_their_own(app, tight_limits):
    app.config['AUTH_MAX_IN_FLIGHT'] = 2
    with app.app_context():
        first = acquire_inflight()
        second = acquire_inflight()
        assert first and second and first != second
        first_token = _lease_token(first)
        second_token = _lease_token(second)
        assert acquire_inflight() is False
        held = AuthAttempt.query.filter_by(
            scope='inflight', seen_values=second_token).one()
        held_until = held.locked_until
        stale = AuthAttempt.query.filter_by(
            scope='inflight', seen_values=first_token).one()
        stale.locked_until = datetime.utcnow() - timedelta(seconds=5)
        db.session.commit()

        third = acquire_inflight()
        assert third and _lease_token(third) != first_token
        third_token = _lease_token(third)
        still_held = AuthAttempt.query.filter_by(
            scope='inflight', seen_values=second_token).one()
        assert still_held.locked_until == held_until
        release_inflight(first_token)
        assert AuthAttempt.query.filter_by(
            scope='inflight', seen_values=second_token).one()
        assert AuthAttempt.query.filter_by(
            scope='inflight', seen_values=third_token).one()
        assert acquire_inflight() is False
        release_inflight(second_token)
        replacement = acquire_inflight()
        assert replacement
        release_inflight(third_token)
        release_inflight(_lease_token(replacement))


def test_ldap_deadline_follows_the_lease_expiry(app, tight_limits, monkeypatch):
    import time as time_module

    from powerdnsadmin.lib import auth_throttle

    start = datetime(2026, 1, 1, 0, 0, 0)
    clock = {'mono': 5000.0, 'wall': start}

    class FrozenDateTime(datetime):
        @classmethod
        def utcnow(cls):
            return clock['wall']

    monkeypatch.setattr(auth_throttle, 'datetime', FrozenDateTime)
    monkeypatch.setattr(time_module, 'monotonic', lambda: clock['mono'])
    monkeypatch.setitem(app.config, 'AUTH_MAX_IN_FLIGHT', 1)
    delayed = {'done': False}
    real_claim = auth_throttle._claim_slot

    def slow_claim(slot, token, now, expires):
        if not delayed['done']:
            delayed['done'] = True
            clock['mono'] += 20
            clock['wall'] = clock['wall'] + timedelta(seconds=20)
        return real_claim(slot, token, now, expires)

    monkeypatch.setattr(auth_throttle, '_claim_slot', slow_claim)
    other = None
    try:
        with app.app_context():
            with auth_throttle.PasswordAttempt(
                    'alice', 'secret', False, '198.51.100.210') as attempt:
                assert attempt.lease
                left = auth_throttle.remaining_authentication_seconds()
                assert 9 <= left <= 10
                clock['mono'] += 10
                clock['wall'] = clock['wall'] + timedelta(seconds=10)
                assert auth_throttle.remaining_authentication_seconds() <= 0
                other = acquire_inflight()
                assert other
                assert _lease_token(other) != attempt.lease
    finally:
        if other:
            with app.app_context():
                release_inflight(_lease_token(other))


def test_one_slot_admits_only_one_worker(app, tight_limits):
    app.config['AUTH_MAX_IN_FLIGHT'] = 1
    barrier = Barrier(8)
    results = []
    lock = Lock()

    def grab(_slot):
        with app.app_context():
            try:
                barrier.wait(timeout=10)
                claimed = acquire_inflight()
                with lock:
                    results.append(claimed[0] if claimed else claimed)
            finally:
                db.session.remove()

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(grab, range(8)))

    held = [token for token in results if token]
    with app.app_context():
        try:
            assert len(held) == 1
            assert len(set(held)) == 1
            live = AuthAttempt.query.filter(
                AuthAttempt.scope == 'inflight',
                AuthAttempt.locked_until > datetime.utcnow(),
            ).count()
            assert live == 1
        finally:
            for token in held:
                release_inflight(token)


def test_workers_cannot_exceed_the_inflight_limit(app, tight_limits):
    app.config['AUTH_MAX_IN_FLIGHT'] = 3
    barrier = Barrier(8)
    results = []
    lock = Lock()

    def grab(_slot):
        with app.app_context():
            try:
                barrier.wait(timeout=10)
                claimed = acquire_inflight()
                with lock:
                    results.append(claimed[0] if claimed else claimed)
            finally:
                db.session.remove()

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(grab, range(8)))

    held = [token for token in results if token]
    with app.app_context():
        try:
            assert len(held) == 3
            live = AuthAttempt.query.filter(
                AuthAttempt.scope == 'inflight',
                AuthAttempt.locked_until > datetime.utcnow(),
            ).count()
            assert live == 3
        finally:
            for token in held:
                release_inflight(token)


def test_closing_an_ldap_budget_returns_429(
        app, client, tight_limits, monkeypatch):
    from powerdnsadmin.models.setting import Setting

    overrides = {
        'ldap_type': 'ldap',
        'ldap_base_dn': 'dc=example,dc=com',
        'ldap_filter_basic': '(objectClass=person)',
        'ldap_filter_username': 'uid',
        'ldap_filter_group': '(objectClass=groupOfNames)',
        'ldap_filter_groupname': 'member',
        'ldap_sg_enabled': False,
    }
    original = Setting.get

    def get(self, name):
        if name in overrides:
            return overrides[name]
        return original(self, name)

    def search(self, search_filter, base_dn, retrieve_attributes=None):
        return [[(
            'uid=test,dc=example,dc=com',
            {'uid': [b'test']},
        )]]

    monkeypatch.setattr(Setting, 'get', get)
    monkeypatch.setattr(User, 'ldap_search', search)
    monkeypatch.setattr(User, 'ldap_auth', lambda self, bind_dn, password: False)
    for name in ('AUTH_SOURCE_LIMIT', 'AUTH_ACCOUNT_LIMIT', 'AUTH_PAIR_LIMIT'):
        app.config[name] = 1

    response = client.get(
        '/api/v1/pdnsadmin/users',
        query_string={'auth_method': 'LDAP'},
        headers=_basic(app.config['TEST_USER'], 'wrong-password'),
        environ_base={'REMOTE_ADDR': '198.51.100.130'},
    )
    assert response.status_code == 429
    assert response.headers['Retry-After']
    assert b'Wrong LDAP configuration' not in response.data


def test_missing_throttle_table_fails_readiness(app, client, monkeypatch):
    monkeypatch.setattr(
        'powerdnsadmin.lib.auth_throttle.throttle_store_ready',
        lambda: False)
    response = client.get('/healthcheck')
    assert response.status_code == 503
    assert b'authentication throttling unavailable' in response.data
    with app.app_context():
        with pytest.raises(RuntimeError):
            assert_throttle_store()


def test_production_refuses_password_checks_without_the_throttle_table(
        app, client, initial_data, monkeypatch):
    monkeypatch.setattr(
        'powerdnsadmin.lib.auth_throttle.acquire_inflight', lambda: None)
    previous = app.config.get('TESTING')
    app.config['TESTING'] = False
    try:
        response = _login(
            client, 'nobody', 'wrong-password', '198.51.100.140')
        assert response.status_code == 503
        assert b'authentication throttling unavailable' in response.data
    finally:
        app.config['TESTING'] = previous


def _api_key_header(token):
    encoded = b64encode(token.encode('utf-8')).decode('utf-8')
    return {'X-API-KEY': encoded}


def _api_key(client, token, ip, path='/api'):
    return client.get(
        path,
        headers=_api_key_header(token),
        environ_base={'REMOTE_ADDR': ip},
    )


def test_invalid_api_keys_are_limited_per_source(
        app, client, tight_limits, monkeypatch, caplog):
    caplog.set_level(logging.WARNING)
    secret = 'UniqueApiKeySecret-not-logged'
    calls = {'n': 0}
    original = ApiKey.get_hashed_password

    def hashed(self, plain_text_password=None):
        calls['n'] += 1
        return original(self, plain_text_password)

    monkeypatch.setattr(ApiKey, 'get_hashed_password', hashed)
    ip = '198.51.100.150'
    other = '198.51.100.151'
    assert _api_key(client, secret, ip).status_code == 401
    assert _api_key(client, 'second-invalid-key', ip).status_code == 401
    blocked = _api_key(client, 'third-invalid-key', ip)
    assert blocked.status_code == 429
    assert blocked.headers['Retry-After']
    assert blocked.get_json()['msg'] == (
        'Too many authentication attempts. Try again later.')
    assert calls['n'] == 3
    again = _api_key(
        client, secret, ip, '/api/v1/servers/localhost/zones')
    assert again.status_code == 429
    assert again.headers['Retry-After']
    assert calls['n'] == 3
    assert _api_key(client, secret, other).status_code == 401
    assert _login(
        client, app.config['TEST_USER'], 'wrong-password', ip
    ).status_code == 200
    assert secret not in caplog.text
    with app.app_context():
        rows = AuthAttempt.query.filter_by(scope='apikey').all()
        assert rows
        for row in rows:
            assert secret not in (row.subject or '')
            assert secret not in (row.seen_values or '')


def test_malformed_api_keys_spend_the_source_budget_without_hashing(
        app, client, tight_limits, monkeypatch):
    calls = {'n': 0}

    def hashed(self, plain_text_password=None):
        calls['n'] += 1
        raise AssertionError('malformed keys must not be hashed')

    monkeypatch.setattr(ApiKey, 'get_hashed_password', hashed)
    ip = '198.51.100.152'
    for header in ('not-valid-base64', 'A' * 1100):
        response = client.get(
            '/api',
            headers={'X-API-KEY': header},
            environ_base={'REMOTE_ADDR': ip},
        )
        assert response.status_code == 401
    blocked = client.get(
        '/api',
        headers={'X-API-KEY': 'A' * 1100},
        environ_base={'REMOTE_ADDR': ip},
    )
    assert blocked.status_code == 429
    assert blocked.headers['Retry-After']
    assert calls['n'] == 0


def test_api_key_concurrency_skips_the_hash(
        app, client, tight_limits, monkeypatch):
    calls = {'n': 0}

    def hashed(self, plain_text_password=None):
        calls['n'] += 1
        return b'unused'

    monkeypatch.setattr(ApiKey, 'get_hashed_password', hashed)
    app.config['AUTH_MAX_IN_FLIGHT'] = 1
    with app.app_context():
        lease = acquire_inflight()
        assert lease
        lease = _lease_token(lease)
    try:
        response = _api_key(client, 'waiting-key', '198.51.100.153')
        assert response.status_code == 429
        assert calls['n'] == 0
    finally:
        with app.app_context():
            release_inflight(lease)


def test_password_lock_does_not_spend_the_api_key_budget(
        app, client, tight_limits):
    ip = '198.51.100.154'
    assert _login(
        client, app.config['TEST_USER'], 'wrong-password', ip
    ).status_code == 200
    assert _login(
        client, app.config['TEST_USER'], 'wrong-password', ip
    ).status_code == 200
    assert _login(
        client, app.config['TEST_USER'], 'wrong-password', ip
    ).status_code == 429
    assert _api_key(client, 'still-an-api-key', ip).status_code == 401
