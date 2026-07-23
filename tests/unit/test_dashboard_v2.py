import base64
from types import SimpleNamespace

import pytest

from powerdnsadmin.routes.dashboard import (
    _validate_dnssec_key_parameters,
    _validate_dnssec_rollover_parameters,
    _reconcile_dnssec_rollover,
)


DNSKEY_PUBLIC = base64.b64encode(bytes(range(64))).decode('ascii')
DNSKEY = '257 3 13 ' + DNSKEY_PUBLIC


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
