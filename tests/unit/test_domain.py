from unittest.mock import MagicMock

from powerdnsadmin.models.domain import Domain


def bare_domain(existing_reverse_zone=None):
    domain = object.__new__(Domain)
    domain.get_id_by_name = MagicMock(
        side_effect=lambda name: (
            1 if name == existing_reverse_zone else None
        ))
    return domain


def test_get_reverse_domain_name_defaults_to_ipv4_parent_zone():
    domain = bare_domain()

    assert domain.get_reverse_domain_name(
        '20.2.0.192.in-addr.arpa.') == '2.0.192.in-addr.arpa'


def test_get_reverse_domain_name_uses_existing_ipv4_parent_zone():
    domain = bare_domain('0.192.in-addr.arpa')

    assert domain.get_reverse_domain_name(
        '20.2.0.192.in-addr.arpa.') == '0.192.in-addr.arpa'


def test_get_reverse_domain_name_defaults_to_ipv6_parent_zone():
    domain = bare_domain()
    reverse_address = (
        '1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.'
        '0.0.0.0.0.0.0.0.8.b.d.0.1.0.0.2.ip6.arpa.'
    )

    assert domain.get_reverse_domain_name(reverse_address) == (
        '0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.'
        '0.0.0.0.0.0.0.8.b.d.0.1.0.0.2.ip6.arpa'
    )
