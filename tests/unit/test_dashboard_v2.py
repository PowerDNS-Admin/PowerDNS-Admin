import base64
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from sqlalchemy import event

from powerdnsadmin.models.base import db
from powerdnsadmin.models.domain import Domain
from powerdnsadmin.models.user import User
from powerdnsadmin.routes.dashboard import (
    _validate_dnssec_key_parameters,
    _validate_dnssec_rollover_parameters,
    _reconcile_dnssec_rollover,
)


DNSKEY_PUBLIC = base64.b64encode(bytes(range(64))).decode('ascii')
DNSKEY = '257 3 13 ' + DNSKEY_PUBLIC


def _authenticate_dashboard_user(app, client, username):
    with app.app_context():
        user_id = User.query.filter_by(username=username).one().id

    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def _dashboard_v2_count_queries(app, client, search=None):
    _authenticate_dashboard_user(
        app, client, app.config['TEST_ADMIN_USER'])

    with app.app_context():
        engine = db.engine

    count_queries = []

    def capture_count_query(conn, cursor, statement, parameters, context,
                            executemany):
        if 'select count(' in statement.lower():
            count_queries.append(statement)

    query = {'length': 10}
    if search is not None:
        query['search[value]'] = search

    event.listen(engine, 'before_cursor_execute', capture_count_query)
    try:
        response = client.get(
            '/dashboard/v2/domains/forward', query_string=query)
    finally:
        event.remove(engine, 'before_cursor_execute', capture_count_query)

    assert response.status_code == 200
    return count_queries


def test_dashboard_v2_reuses_total_count_without_search(app, client,
                                                         initial_data):
    count_queries = _dashboard_v2_count_queries(app, client)

    assert len(count_queries) == 1


def test_dashboard_v2_counts_filtered_domains_when_searching(app, client,
                                                              initial_data):
    count_queries = _dashboard_v2_count_queries(app, client, search='example')

    assert len(count_queries) == 2


@pytest.mark.parametrize(
    'url',
    [
        '/dashboard/',
        '/dashboard/v2/domains/forward?refresh=1&length=10',
    ],
)
def test_regular_user_cannot_trigger_global_domain_sync(app, client,
                                                         initial_data, url):
    _authenticate_dashboard_user(app, client, app.config['TEST_USER'])

    with patch.object(Domain, 'update') as update_domains, \
            patch('powerdnsadmin.routes.dashboard.render_template',
                  return_value=''):
        response = client.get(url)

    assert response.status_code == 200
    update_domains.assert_not_called()


@pytest.mark.parametrize(
    'url',
    [
        '/dashboard/',
        '/dashboard/v2/domains/forward?refresh=1&length=10',
    ],
)
def test_administrator_can_trigger_global_domain_sync(app, client,
                                                       initial_data, url):
    _authenticate_dashboard_user(
        app, client, app.config['TEST_ADMIN_USER'])

    with patch.object(Domain, 'update') as update_domains, \
            patch('powerdnsadmin.routes.dashboard.render_template',
                  return_value=''):
        response = client.get(url)

    assert response.status_code == 200
    update_domains.assert_called_once_with()


def test_dashboard_v2_does_not_request_initial_refresh_for_regular_user(
        app, client, initial_data):
    _authenticate_dashboard_user(app, client, app.config['TEST_USER'])

    with patch('powerdnsadmin.routes.dashboard.render_template',
               return_value='') as render:
        response = client.get('/dashboard/v2/')

    assert response.status_code == 200
    assert render.call_args.kwargs['refresh_on_first_load'] is False


def _rollover_reference(backend_key_id=10):
    from powerdnsadmin.services.dnssec import (
        dnskey_fingerprint, dnskey_key_tag)
    return SimpleNamespace(
        role='new',
        backend_key_id=backend_key_id,
        fingerprint=dnskey_fingerprint(DNSKEY),
        key_tag=dnskey_key_tag(DNSKEY),
    )


def _backend_key(key_id, dnskey=DNSKEY):
    return {
        'id': key_id,
        'keytype': 'csk',
        'algorithm': 'ECDSAP256SHA256',
        'bits': 256,
        'dnskey': dnskey,
        'ds': [],
    }


def test_rollover_reconciliation_refreshes_backend_local_key_id():
    reference = _rollover_reference()
    rollover = SimpleNamespace(
        key_references=[reference], old_keys=[], new_keys=[10])

    result = _reconcile_dnssec_rollover(rollover, [_backend_key(77)])

    assert result['state'] == 'ok'
    assert result['changed'] is True
    assert reference.backend_key_id == 77
    assert rollover.new_keys == [77]


def test_rollover_reconciliation_blocks_missing_public_key():
    rollover = SimpleNamespace(
        key_references=[_rollover_reference()], old_keys=[], new_keys=[10])

    result = _reconcile_dnssec_rollover(rollover, [])

    assert result['state'] == 'needs_reconciliation'
    assert result['issues'][0]['reason'] == 'missing_key'


def test_rollover_reconciliation_blocks_ambiguous_public_key():
    rollover = SimpleNamespace(
        key_references=[_rollover_reference()], old_keys=[], new_keys=[10])

    result = _reconcile_dnssec_rollover(
        rollover, [_backend_key(77), _backend_key(78)])

    assert result['state'] == 'needs_reconciliation'
    assert result['issues'][0]['reason'] == 'ambiguous_key'


@pytest.mark.parametrize(
    'parameters',
    [
        {'keytype': 'csk', 'algorithm': 'ecdsa256', 'bits': '256'},
        {'keytype': 'ksk', 'algorithm': 'ecdsa384', 'bits': '384'},
        {'keytype': 'zsk', 'algorithm': 'ed25519', 'bits': '256'},
        {'keytype': 'csk', 'algorithm': 'ed448', 'bits': '456'},
        {'keytype': 'ksk', 'algorithm': 'rsasha256', 'bits': '2048'},
        {'keytype': 'zsk', 'algorithm': 'rsasha512', 'bits': '4096'},
    ],
)
def test_dnssec_v2_accepts_supported_key_parameters(parameters):
    validated, error = _validate_dnssec_key_parameters(parameters)

    assert error is None
    assert validated == {
        'keytype': parameters['keytype'],
        'algorithm': parameters['algorithm'],
        'bits': int(parameters['bits']),
        'active': True,
        'published': True,
    }


@pytest.mark.parametrize(
    ('parameters', 'message'),
    [
        ({'keytype': 'invalid', 'algorithm': 'ecdsa256', 'bits': '256'},
         'supported DNSSEC key type'),
        ({'keytype': 'csk', 'algorithm': 'rsasha1', 'bits': '2048'},
         'supported DNSSEC algorithm'),
        ({'keytype': 'csk', 'algorithm': 'ecdsa256', 'bits': '2048'},
         'not valid for this algorithm'),
        ({'keytype': 'csk', 'algorithm': 'rsasha256', 'bits': 'not-a-number'},
         'valid DNSSEC key size'),
    ],
)
def test_dnssec_v2_rejects_unsupported_key_parameters(parameters, message):
    validated, error = _validate_dnssec_key_parameters(parameters)

    assert validated is None
    assert message in error


def test_csk_rollover_stages_second_active_published_key():
    rollover, error = _validate_dnssec_rollover_parameters({
        'rollover_type': 'csk',
        'keytype': 'csk',
        'algorithm': 'ecdsa256',
        'bits': '256',
    }, [{
        'id': 10,
        'keytype': 'csk',
        'algorithm': 'ECDSAP256SHA256',
        'active': True,
        'published': True,
    }])

    assert error is None
    assert rollover['old_key_ids'] == [10]
    assert rollover['key_parameters']['active'] is True
    assert rollover['key_parameters']['published'] is True


def test_zsk_rollover_pre_publishes_inactive_key():
    rollover, error = _validate_dnssec_rollover_parameters({
        'rollover_type': 'zsk',
        'keytype': 'zsk',
        'algorithm': 'rsasha256',
        'bits': '2048',
    }, [{
        'id': 11,
        'keytype': 'zsk',
        'algorithm': 'RSASHA256',
        'active': True,
        'published': True,
    }])

    assert error is None
    assert rollover['key_parameters']['active'] is False
    assert rollover['key_parameters']['published'] is True


def test_algorithm_rollover_stages_active_unpublished_key():
    rollover, error = _validate_dnssec_rollover_parameters({
        'rollover_type': 'algorithm',
        'keytype': 'csk',
        'algorithm': 'ed25519',
        'bits': '256',
    }, [{
        'id': 12,
        'keytype': 'csk',
        'algorithm': 'ECDSAP256SHA256',
        'active': True,
        'published': True,
    }])

    assert error is None
    assert rollover['key_parameters']['active'] is True
    assert rollover['key_parameters']['published'] is False


def test_role_rollover_rejects_implicit_algorithm_change():
    rollover, error = _validate_dnssec_rollover_parameters({
        'rollover_type': 'csk',
        'keytype': 'csk',
        'algorithm': 'ed25519',
        'bits': '256',
    }, [{
        'id': 13,
        'keytype': 'csk',
        'algorithm': 'ECDSAP256SHA256',
        'active': True,
        'published': True,
    }])

    assert rollover is None
    assert 'Algorithm rollover' in error


def test_algorithm_rollover_requires_a_different_algorithm():
    rollover, error = _validate_dnssec_rollover_parameters({
        'rollover_type': 'algorithm',
        'keytype': 'csk',
        'algorithm': 'ecdsa256',
        'bits': '256',
    }, [{
        'id': 14,
        'keytype': 'csk',
        'algorithm': 'ECDSAP256SHA256',
        'active': True,
        'published': True,
    }])

    assert rollover is None
    assert 'different algorithm' in error
