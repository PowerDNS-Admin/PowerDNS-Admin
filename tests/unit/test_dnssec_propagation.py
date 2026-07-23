import base64
from types import SimpleNamespace

import dns.flags
import dns.message
import dns.name
import dns.rrset

from powerdnsadmin.services import dnssec as dnssec_service


DS_SHA256 = '12345 13 2 ' + ('AABBCCDD' * 8)
DS_SHA384 = '12345 13 4 ' + ('0011223344556677' * 6)
DNSKEY_PUBLIC = base64.b64encode(bytes(range(64))).decode('ascii')
DNSKEY = '257 3 13 ' + DNSKEY_PUBLIC


def test_dnskey_identity_is_stable_and_contains_only_public_data():
    key = {
        'id': 41,
        'keytype': 'CSK',
        'algorithm': 'ECDSAP256SHA256',
        'bits': 256,
        'dnskey': '  257  3 13\n' + DNSKEY_PUBLIC.rstrip('=') + '  ',
        'ds': [DS_SHA256.lower()],
        'privatekey': 'must-not-be-persisted',
    }

    identity = dnssec_service.dnssec_key_identity(key)

    assert identity['dnskey'] == DNSKEY
    assert identity['fingerprint'] == dnssec_service.dnskey_fingerprint(DNSKEY)
    assert identity['keyTag'] == dnssec_service.dnskey_key_tag(DNSKEY)
    assert identity['keyType'] == 'csk'
    assert identity['ds'] == [DS_SHA256]
    assert 'privatekey' not in identity


def test_dnssec_ds_expectations_only_include_active_published_sep_keys():
    keys = [
        {
            'id': 1,
            'keytype': 'csk',
            'active': True,
            'published': True,
            'algorithm': 'ECDSAP256SHA256',
            'ds': ['  ' + DS_SHA256.lower().replace(' ', '  ') + '  ', DS_SHA384],
        },
        {
            'id': 2,
            'keytype': 'zsk',
            'active': True,
            'published': True,
            'ds': [DS_SHA256],
        },
        {
            'id': 3,
            'keytype': 'ksk',
            'active': False,
            'published': True,
            'ds': [DS_SHA256],
        },
        {
            'id': 4,
            'keytype': 'ksk',
            'active': True,
            'published': False,
            'ds': [DS_SHA256],
        },
    ]

    assert dnssec_service.dnssec_ds_expectations(keys) == [{
        'keyId': 1,
        'keyType': 'csk',
        'algorithm': 'ECDSAP256SHA256',
        'ds': [DS_SHA256, DS_SHA384],
    }]


def test_parent_nameserver_matches_any_digest_for_each_expected_key(monkeypatch):
    zone_name = dns.name.from_text('example.org.')
    query_response = dns.message.make_response(
        dns.message.make_query(zone_name, 'DS'))
    query_response.flags |= dns.flags.AA
    query_response.answer.append(dns.rrset.from_text(
        zone_name, 300, 'IN', 'DS', DS_SHA256))

    monkeypatch.setattr(
        dnssec_service.dns.query, 'udp',
        lambda query, address, timeout: query_response)

    result = dnssec_service._query_parent_nameserver(
        zone_name,
        'a0.org.afilias-nst.info.',
        ['192.0.2.53'],
        [{
            'keyId': 7,
            'keyType': 'csk',
            'algorithm': 'ECDSAP256SHA256',
            'ds': [DS_SHA256, DS_SHA384],
        }],
        1.0,
    )

    assert result['authoritative'] is True
    assert result['matches'] is True
    assert result['matchedKeyIds'] == [7]
    assert result['ds'] == [DS_SHA256]


def test_check_parent_ds_reports_partial_propagation(monkeypatch):
    resolver = SimpleNamespace()
    parent_zone = dns.name.from_text('org.')
    nameservers = [
        SimpleNamespace(target=dns.name.from_text('ns1.example.')),
        SimpleNamespace(target=dns.name.from_text('ns2.example.')),
    ]
    resolver.resolve = lambda name, record_type, lifetime: nameservers

    monkeypatch.setattr(
        dnssec_service.dns.resolver, 'zone_for_name',
        lambda name, resolver, lifetime: parent_zone)
    monkeypatch.setattr(
        dnssec_service, '_resolve_nameserver_addresses',
        lambda resolver, nameserver, timeout: (['192.0.2.53'], []))

    def query(zone_name, nameserver, addresses, expectations, timeout):
        matches = nameserver == 'ns1.example.'
        return {
            'nameserver': nameserver,
            'addresses': addresses,
            'queriedAddress': addresses[0],
            'authoritative': True,
            'responseCode': 'NOERROR',
            'ds': [DS_SHA256] if matches else [],
            'matchedKeyIds': [1] if matches else [],
            'matches': matches,
            'error': None,
        }

    monkeypatch.setattr(dnssec_service, '_query_parent_nameserver', query)

    result = dnssec_service.check_parent_ds(
        'example.org.',
        [{
            'id': 1,
            'keytype': 'csk',
            'active': True,
            'published': True,
            'algorithm': 'ECDSAP256SHA256',
            'ds': [DS_SHA256],
        }],
        resolver=resolver,
    )

    assert result['state'] == 'partial'
    assert result['parentZone'] == 'org.'
    assert result['summary'] == {
        'totalNameservers': 2,
        'checkedNameservers': 2,
        'matchedNameservers': 1,
        'failedNameservers': 0,
    }


def test_check_parent_ds_skips_dns_when_no_sep_key():
    result = dnssec_service.check_parent_ds(
        'example.org.',
        [{
            'id': 1,
            'keytype': 'zsk',
            'active': True,
            'published': True,
            'ds': [],
        }],
    )

    assert result['state'] == 'not_applicable'
    assert result['nameservers'] == []


def test_check_parent_ds_reports_undelegated_zone(monkeypatch):
    resolver = SimpleNamespace()
    parent_zone = dns.name.root
    resolver.resolve = lambda name, record_type, lifetime: [
        SimpleNamespace(target=dns.name.from_text('a.root-servers.net.')),
    ]
    monkeypatch.setattr(
        dnssec_service.dns.resolver, 'zone_for_name',
        lambda name, resolver, lifetime: parent_zone)
    monkeypatch.setattr(
        dnssec_service, '_resolve_nameserver_addresses',
        lambda resolver, nameserver, timeout: (['192.0.2.53'], []))
    monkeypatch.setattr(
        dnssec_service, '_query_parent_nameserver',
        lambda zone_name, nameserver, addresses, expectations, timeout: {
            'nameserver': nameserver,
            'addresses': addresses,
            'queriedAddress': addresses[0],
            'authoritative': True,
            'responseCode': 'NXDOMAIN',
            'delegated': False,
            'ds': [],
            'matchedKeyIds': [],
            'matches': False,
            'error': None,
        })

    result = dnssec_service.check_parent_ds(
        '1.1.',
        [{
            'id': 1,
            'keytype': 'csk',
            'active': True,
            'published': True,
            'algorithm': 'ECDSAP256SHA256',
            'ds': [DS_SHA256],
        }],
        resolver=resolver,
    )

    assert result['state'] == 'undelegated'
    assert result['parentZone'] == '.'
