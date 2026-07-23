"""DNSSEC delegation inspection helpers.

The checks in this module deliberately query the authoritative nameservers for
the parent zone. A recursive resolver can return a cached DS answer and hide a
partially propagated registrar update.
"""

import concurrent.futures
import base64
import binascii
import datetime
import hashlib

import dns.exception
import dns.flags
import dns.message
import dns.name
import dns.query
import dns.rcode
import dns.rdatatype
import dns.resolver


DNS_QUERY_TIMEOUT = 2.0
MAX_PARENT_NAMESERVERS = 16
MAX_NAMESERVER_ADDRESSES = 4


def canonical_dnskey(dnskey):
    """Normalize public DNSKEY RDATA without changing its key material."""
    fields = str(dnskey or '').split()
    if len(fields) < 4:
        raise ValueError('PowerDNS did not return complete DNSKEY data.')
    try:
        flags = int(fields[0])
        protocol = int(fields[1])
        algorithm = int(fields[2])
    except (TypeError, ValueError) as error:
        raise ValueError('PowerDNS returned invalid DNSKEY data.') from error
    public_key = ''.join(fields[3:]).rstrip('=')
    try:
        decoded_public_key = base64.b64decode(
            public_key + ('=' * (-len(public_key) % 4)), validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError('PowerDNS returned invalid DNSKEY key material.') from error
    public_key = base64.b64encode(decoded_public_key).decode('ascii')
    return '{} {} {} {}'.format(flags, protocol, algorithm, public_key)


def dnskey_fingerprint(dnskey):
    """Return a stable SHA-256 identity for public DNSKEY RDATA."""
    canonical = canonical_dnskey(dnskey)
    return hashlib.sha256(canonical.encode('ascii')).hexdigest()


def dnskey_key_tag(dnskey):
    """Calculate the RFC 4034 key tag for public DNSKEY RDATA."""
    canonical = canonical_dnskey(dnskey)
    flags, protocol, algorithm, public_key = canonical.split(' ', 3)
    wire = (
        int(flags).to_bytes(2, byteorder='big')
        + bytes((int(protocol), int(algorithm)))
        + base64.b64decode(public_key)
    )
    accumulator = 0
    for index, value in enumerate(wire):
        accumulator += value << 8 if index % 2 == 0 else value
    accumulator += (accumulator >> 16) & 0xFFFF
    return accumulator & 0xFFFF


def dnssec_key_identity(key):
    """Build the public, backend-independent identity stored for a key."""
    dnskey = canonical_dnskey(key.get('dnskey'))
    algorithm = str(key.get('algorithm') or '')
    keytype = str(key.get('keytype') or '').lower()
    if not algorithm or not keytype:
        raise ValueError('PowerDNS did not return the DNSSEC key role and algorithm.')
    return {
        'backendKeyId': int(key['id']),
        'fingerprint': dnskey_fingerprint(dnskey),
        'keyTag': dnskey_key_tag(dnskey),
        'keyType': keytype,
        'algorithm': algorithm,
        'bits': key.get('bits'),
        'dnskey': dnskey,
        'ds': sorted({
            normalize_ds(record) for record in key.get('ds', [])
            if str(record).strip()
        }),
    }


def normalize_ds(value):
    """Return a stable representation for comparing DS record text."""
    return ' '.join(str(value).split()).upper()


def dnssec_ds_expectations(keys):
    """Group acceptable DS digests by active, published SEP key."""
    expectations = []
    for key in keys:
        keytype = str(key.get('keytype', '')).lower()
        if (keytype not in ('ksk', 'csk') or not key.get('active')
                or not key.get('published')):
            continue

        ds_records = sorted({
            normalize_ds(record)
            for record in key.get('ds', [])
            if str(record).strip()
        })
        if not ds_records:
            continue

        expectations.append({
            'keyId': key.get('id'),
            'keyType': keytype,
            'algorithm': key.get('algorithm'),
            'ds': ds_records,
        })
    return expectations


def _resolve_nameserver_addresses(resolver, nameserver, timeout):
    addresses = []
    errors = []
    for record_type in ('A', 'AAAA'):
        try:
            answer = resolver.resolve(
                nameserver, record_type, lifetime=timeout)
            for record in answer:
                address = getattr(record, 'address', record.to_text())
                if address not in addresses:
                    addresses.append(address)
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            continue
        except (dns.exception.DNSException, OSError) as error:
            errors.append(str(error))

    return addresses[:MAX_NAMESERVER_ADDRESSES], errors


def _query_parent_nameserver(zone_name, nameserver, addresses,
                             expectations, timeout):
    result = {
        'nameserver': nameserver,
        'addresses': addresses,
        'queriedAddress': None,
        'authoritative': False,
        'responseCode': None,
        'delegated': None,
        'ds': [],
        'matchedKeyIds': [],
        'matches': False,
        'error': None,
    }
    if not addresses:
        result['error'] = 'No IPv4 or IPv6 address could be resolved.'
        return result

    query = dns.message.make_query(
        zone_name, dns.rdatatype.DS, want_dnssec=True)
    query_errors = []
    for address in addresses:
        try:
            response = dns.query.udp(query, address, timeout=timeout)
            if response.flags & dns.flags.TC:
                response = dns.query.tcp(query, address, timeout=timeout)

            result['queriedAddress'] = address
            result['authoritative'] = bool(response.flags & dns.flags.AA)
            result['responseCode'] = dns.rcode.to_text(response.rcode())
            if response.rcode() == dns.rcode.NXDOMAIN:
                result['delegated'] = False
            if response.rcode() not in (dns.rcode.NOERROR, dns.rcode.NXDOMAIN):
                query_errors.append(
                    '{} returned {}'.format(address, result['responseCode']))
                continue
            if not result['authoritative']:
                query_errors.append(
                    '{} returned a non-authoritative answer'.format(address))
                continue

            records = set()
            for rrset in response.answer:
                if rrset.rdtype == dns.rdatatype.DS and rrset.name == zone_name:
                    records.update(normalize_ds(record.to_text())
                                   for record in rrset)
            result['ds'] = sorted(records)

            if result['delegated'] is None:
                delegation_query = dns.message.make_query(
                    zone_name, dns.rdatatype.NS)
                delegation_response = dns.query.udp(
                    delegation_query, address, timeout=timeout)
                if delegation_response.flags & dns.flags.TC:
                    delegation_response = dns.query.tcp(
                        delegation_query, address, timeout=timeout)
                result['delegated'] = any(
                    rrset.rdtype == dns.rdatatype.NS
                    and rrset.name == zone_name
                    for section in (
                        delegation_response.answer,
                        delegation_response.authority,
                    )
                    for rrset in section
                )

            matched_key_ids = []
            for expectation in expectations:
                if records.intersection(expectation['ds']):
                    matched_key_ids.append(expectation['keyId'])
            result['matchedKeyIds'] = matched_key_ids
            # A delegation remains valid when each parent nameserver serves a
            # DS for at least one active, published SEP key. Per-key rollout
            # status is calculated separately below.
            result['matches'] = bool(matched_key_ids)
            return result
        except (dns.exception.DNSException, OSError) as error:
            query_errors.append('{}: {}'.format(address, error))

    result['error'] = '; '.join(query_errors) or 'The nameserver did not respond.'
    return result


def check_parent_ds(domain_name, keys, resolver=None,
                    timeout=DNS_QUERY_TIMEOUT):
    """Check whether each active published KSK/CSK has reached the parent.

    A key can expose several DS digest variants. A parent nameserver matches a
    key when it serves at least one of those variants. Full propagation means
    every discovered parent nameserver authoritatively serves a DS for every
    expected key.
    """
    checked_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    expectations = dnssec_ds_expectations(keys)
    result = {
        'state': 'not_applicable',
        'checkedAt': checked_at,
        'parentZone': None,
        'expectedKeys': expectations,
        'nameservers': [],
        'summary': {
            'totalNameservers': 0,
            'checkedNameservers': 0,
            'matchedNameservers': 0,
            'failedNameservers': 0,
        },
        'error': None,
    }
    if not expectations:
        return result

    try:
        zone_name = dns.name.from_text(domain_name)
        if not zone_name.is_absolute():
            zone_name = zone_name.concatenate(dns.name.root)
        if zone_name == dns.name.root:
            raise ValueError('The DNS root does not have a registrar parent.')

        resolver = resolver or dns.resolver.Resolver()
        parent_zone = dns.resolver.zone_for_name(
            zone_name.parent(), resolver=resolver, lifetime=timeout)
        result['parentZone'] = parent_zone.to_text()

        answer = resolver.resolve(
            parent_zone, dns.rdatatype.NS, lifetime=timeout)
        nameservers = sorted({record.target.to_text() for record in answer})
        nameservers = nameservers[:MAX_PARENT_NAMESERVERS]
        if not nameservers:
            raise dns.resolver.NoAnswer('The parent zone returned no NS records.')

        def resolve_addresses(nameserver):
            addresses, address_errors = _resolve_nameserver_addresses(
                resolver, nameserver, timeout)
            return {
                'nameserver': nameserver,
                'addresses': addresses,
                'addressError': (
                    '; '.join(address_errors) if not addresses else None),
            }

        worker_count = min(8, len(nameservers))
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=worker_count) as executor:
            resolved_nameservers = list(
                executor.map(resolve_addresses, nameservers))

        def query(item):
            nameserver_result = _query_parent_nameserver(
                zone_name, item['nameserver'], item['addresses'],
                expectations, timeout)
            if item['addressError'] and nameserver_result['error']:
                nameserver_result['error'] = '{} {}'.format(
                    nameserver_result['error'], item['addressError']).strip()
            return nameserver_result

        worker_count = min(8, len(resolved_nameservers))
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=worker_count) as executor:
            result['nameservers'] = list(
                executor.map(query, resolved_nameservers))
    except (dns.exception.DNSException, ValueError, OSError) as error:
        result['state'] = 'error'
        result['error'] = str(error)
        return result

    total = len(result['nameservers'])
    checked = sum(1 for item in result['nameservers'] if not item['error'])
    matched = sum(1 for item in result['nameservers'] if item['matches'])
    failed = total - checked
    result['summary'] = {
        'totalNameservers': total,
        'checkedNameservers': checked,
        'matchedNameservers': matched,
        'failedNameservers': failed,
    }

    delegated_results = [
        item['delegated'] for item in result['nameservers']
        if not item['error'] and item.get('delegated') is not None
    ]

    for expectation in result['expectedKeys']:
        key_matches = sum(
            1 for item in result['nameservers']
            if expectation['keyId'] in item['matchedKeyIds'])
        expectation['matchedNameservers'] = key_matches
        expectation['totalNameservers'] = total
        expectation['propagated'] = (
            total > 0 and failed == 0 and key_matches == total)

    if checked == 0:
        result['state'] = 'error'
        result['error'] = 'No parent authoritative nameserver could be checked.'
    elif delegated_results and not any(delegated_results):
        result['state'] = 'undelegated'
    elif matched == total and failed == 0:
        result['state'] = 'propagated'
    elif matched > 0:
        result['state'] = 'partial'
    else:
        result['state'] = 'missing'
    return result
