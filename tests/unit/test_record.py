from copy import deepcopy
from unittest.mock import MagicMock, call, patch

import pytest

from powerdnsadmin.models.record import Record


@pytest.fixture
def record_model(app):
    settings = {
        'pdns_api_url': 'http://powerdns.test/',
        'pdns_api_key': 'test-key',
        'pdns_api_timeout': 5,
        'verify_ssl_connections': False,
        'pretty_ipv6_ptr': False,
        'auto_ptr': False,
    }

    with app.app_context(), patch(
            'powerdnsadmin.models.record.Setting') as setting:
        setting.return_value.get.side_effect = settings.get
        setting.return_value.get_records_allow_to_edit.return_value = [
            'A', 'AAAA', 'CNAME', 'PTR', 'SOA', 'TXT'
        ]
        yield Record(), settings, setting


def submitted_record(name='www', record_type='A', data='192.0.2.1',
                     status='Active', ttl='300', comment=''):
    return {
        'record_name': name,
        'record_type': record_type,
        'record_data': data,
        'record_status': status,
        'record_ttl': ttl,
        'record_comment': comment,
    }


def test_get_rrsets_discards_empty_records_and_aligns_sorted_comments(
        record_model):
    record, _, _ = record_model
    response = {
        'rrsets': [{
            'name': 'www.example.org.',
            'type': 'A',
            'records': [
                {'content': '192.0.2.2', 'disabled': False},
                {'content': '192.0.2.1', 'disabled': False},
            ],
            'comments': [{'content': 'second', 'account': ''}],
        }, {
            'name': 'empty.example.org.',
            'type': 'TXT',
            'records': [],
            'comments': [],
        }]
    }

    with patch('powerdnsadmin.models.record.utils.fetch_json',
               return_value=response) as fetch_json:
        result = record.get_rrsets('example.org')

    assert len(result) == 1
    assert [item['content'] for item in result[0]['records']] == [
        '192.0.2.1', '192.0.2.2'
    ]
    assert [item['content'] for item in result[0]['comments']] == [
        '', 'second'
    ]
    assert fetch_json.call_args.kwargs == {
        'timeout': 5,
        'headers': {'X-API-Key': 'test-key'},
        'verify': False,
    }


def test_get_rrsets_returns_empty_list_when_powerdns_fails(record_model):
    record, _, _ = record_model
    with patch('powerdnsadmin.models.record.utils.fetch_json',
               side_effect=RuntimeError('unavailable')):
        assert record.get_rrsets('example.org') == []


def test_add_rejects_conflicting_address_or_cname(record_model):
    record, _, _ = record_model
    record.name = 'www.example.org.'
    with patch.object(record, 'get_rrsets', return_value=[{
            'name': record.name,
            'type': 'AAAA',
            'records': [{'content': '2001:db8::1'}],
    }]), patch('powerdnsadmin.models.record.utils.fetch_json') as fetch_json:
        result = record.add('example.org', {'rrsets': []})

    assert result['status'] == 'error'
    assert 'already exists' in result['msg']
    fetch_json.assert_not_called()


def test_add_allows_same_name_for_non_conflicting_record_type(record_model):
    record, _, _ = record_model
    record.name = 'shared.example.org.'
    payload = {'rrsets': [{'name': record.name, 'type': 'A'}]}

    with patch.object(record, 'get_rrsets', return_value=[{
            'name': record.name,
            'type': 'TXT',
            'records': [{'content': 'existing'}],
    }]), patch('powerdnsadmin.models.record.utils.fetch_json',
               return_value={}) as fetch_json:
        result = record.add('example.org', payload)

    assert result['status'] == 'ok'
    assert fetch_json.call_args.kwargs['data'] == payload


@pytest.mark.parametrize('raises, expected_status', [
    (False, 'ok'),
    (True, 'error'),
])
def test_add_reports_powerdns_result(record_model, raises, expected_status):
    record, _, _ = record_model
    record.name = 'new.example.org.'
    payload = {'rrsets': [{'name': record.name}]}
    side_effect = RuntimeError('unavailable') if raises else None

    with patch.object(record, 'get_rrsets', return_value=[]), patch(
            'powerdnsadmin.models.record.utils.fetch_json',
            return_value={}, side_effect=side_effect) as fetch_json:
        result = record.add('example.org', payload)

    assert result['status'] == expected_status
    assert fetch_json.call_args.kwargs['method'] == 'PATCH'
    assert fetch_json.call_args.kwargs['data'] == payload


def test_merge_rrsets_validates_and_merges_sorted_pairs(record_model):
    record, _, _ = record_model
    with pytest.raises(Exception, match='Empty rrsets'):
        record.merge_rrsets([])

    single = {'records': [], 'comments': []}
    assert record.merge_rrsets([single]) is single

    merged = record.merge_rrsets([{
        'name': 'www.example.org.',
        'type': 'A',
        'records': [{'content': '192.0.2.2', 'disabled': False}],
        'comments': [{'content': 'second', 'account': ''}],
    }, {
        'name': 'www.example.org.',
        'type': 'A',
        'records': [{'content': '192.0.2.1', 'disabled': True}],
        'comments': [],
    }])

    assert [item['content'] for item in merged['records']] == [
        '192.0.2.1', '192.0.2.2'
    ]
    assert [item['content'] for item in merged['comments']] == ['', 'second']


def test_build_rrsets_formats_names_content_status_and_groups(record_model):
    record, _, _ = record_model
    records = [
        submitted_record(name='@', record_type='MX', data='10 mail.[ZONE]',
                         comment='primary'),
        submitted_record(name='www', data='192.0.2.2', status='Disabled'),
        submitted_record(name='www', data='192.0.2.1'),
        submitted_record(name='café', record_type='CNAME',
                         data='tärget.example'),
    ]

    result = record.build_rrsets('example.org', records)

    by_key = {(rrset['name'], rrset['type']): rrset for rrset in result}
    root_mx = by_key[('example.org.', 'MX')]
    assert root_mx['records'][0]['content'] == '10 mail.example.org.'
    assert root_mx['comments'][0]['content'] == 'primary'

    addresses = by_key[('www.example.org.', 'A')]
    assert addresses['ttl'] == 300
    assert addresses['records'] == [
        {'content': '192.0.2.1', 'disabled': False},
        {'content': '192.0.2.2', 'disabled': True},
    ]

    cname = by_key[('xn--caf-dma.example.org.', 'CNAME')]
    assert cname['records'][0]['content'] == 'xn--trget-gra.example.'


def test_build_rrsets_supports_pretty_ipv6_ptr(record_model):
    record, _, _ = record_model
    record.PRETTY_IPV6_PTR = True

    result = record.build_rrsets(
        '8.b.d.0.1.0.0.2.ip6.arpa',
        [submitted_record(name='2001:db8::1', record_type='PTR',
                          data='host.example.org')],
    )

    assert result[0]['name'] == (
        '1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.'
        '0.0.0.0.0.0.0.0.8.b.d.0.1.0.0.2.ip6.arpa.'
    )
    assert result[0]['records'][0]['content'] == 'host.example.org.'


def test_compare_builds_editable_replacements_and_deletions(record_model):
    record, _, _ = record_model
    unchanged = {
        'name': 'same.example.org.', 'type': 'TXT', 'ttl': 300,
        'records': [{'content': 'same', 'disabled': False}],
        'comments': [{'content': '', 'account': ''}],
    }
    old = {
        'name': 'old.example.org.', 'type': 'A', 'ttl': 300,
        'records': [{'content': '192.0.2.1', 'disabled': False}],
        'comments': [{'content': 'old', 'account': '', 'modified_at': 1}],
    }
    soa = {
        'name': 'example.org.', 'type': 'SOA', 'ttl': 3600,
        'records': [{'content': 'soa data', 'disabled': False}],
        'comments': [],
    }
    unsupported = {
        'name': 'ignored.example.org.', 'type': 'CAA', 'ttl': 300,
        'records': [{'content': 'ignored', 'disabled': False}],
        'comments': [],
    }
    added = {
        'name': 'new.example.org.', 'type': 'A', 'ttl': 300,
        'records': [{'content': '192.0.2.2', 'disabled': False}],
        'comments': [{'content': '', 'account': ''}],
    }

    with patch.object(record, 'build_rrsets',
                      return_value=[unchanged, added]), patch.object(
                          record, 'get_rrsets',
                          return_value=[unchanged, old, soa, unsupported]):
        new, deleted, has_comments = record.compare('example.org', [])

    assert new['rrsets'] == [dict(added, changetype='REPLACE')]
    assert deleted['rrsets'] == [dict(old, changetype='DELETE')]
    assert has_comments is True
    assert 'modified_at' not in old['comments'][0]


def test_apply_rrsets_sends_patch_to_powerdns(record_model):
    record, _, _ = record_model
    payload = {'rrsets': [{'name': 'www.example.org.', 'type': 'A'}]}

    with patch('powerdnsadmin.models.record.utils.fetch_json',
               return_value={'result': 'ok'}) as fetch_json:
        result = record.apply_rrsets('example.org', payload)

    assert result == {'result': 'ok'}
    assert fetch_json.call_args.args[0] == (
        'http://powerdns.test/api/v1/servers/localhost/zones/example.org')
    assert fetch_json.call_args.kwargs == {
        'headers': {
            'X-API-Key': 'test-key',
            'Content-Type': 'application/json',
        },
        'method': 'PATCH',
        'verify': False,
        'data': payload,
    }


@pytest.mark.parametrize('comments_supported, expected_comments_present', [
    (True, True),
    (False, False),
])
def test_to_api_payload_handles_empty_comments_without_mutating_input(
        comments_supported, expected_comments_present):
    replacement = {
        'name': 'www.example.org.', 'type': 'A', 'ttl': 300,
        'changetype': 'REPLACE',
        'records': [{'content': '192.0.2.1', 'disabled': False}],
        'comments': [{'content': '', 'account': ''}],
    }
    original = deepcopy(replacement)

    payload = Record.to_api_payload([replacement], [], comments_supported)

    assert ('comments' in payload['rrsets'][0]) is expected_comments_present
    if expected_comments_present:
        assert payload['rrsets'][0]['comments'] == []
    assert replacement == original


def test_to_api_payload_minifies_deletes_and_suppresses_replaced_key():
    deleted = [{
        'name': 'old.example.org.', 'type': 'A', 'ttl': 300,
        'changetype': 'DELETE', 'records': [], 'comments': [],
    }, {
        'name': 'same.example.org.', 'type': 'TXT', 'ttl': 300,
        'changetype': 'DELETE', 'records': [], 'comments': [],
    }]
    replacements = [{
        'name': 'same.example.org.', 'type': 'TXT', 'ttl': 300,
        'changetype': 'REPLACE',
        'records': [{'content': 'new', 'disabled': False}],
        'comments': [{'content': 'kept', 'account': ''}],
    }]

    payload = Record.to_api_payload(replacements, deleted, True)

    assert payload['rrsets'][0] == {
        'name': 'old.example.org.', 'type': 'A', 'changetype': 'DELETE'
    }
    assert payload['rrsets'][1] == replacements[0]


def test_to_api_payload_passes_through_unrecognized_change_types():
    replacement = {
        'name': 'new.example.org.',
        'type': 'A',
        'changetype': 'UNCHANGED',
    }
    deletion = {
        'name': 'old.example.org.',
        'type': 'A',
        'changetype': 'UNCHANGED',
    }

    payload = Record.to_api_payload([replacement], [deletion], False)

    assert payload == {'rrsets': [deletion, replacement]}


def test_apply_skips_empty_patch_then_runs_follow_up_tasks(record_model):
    record, _, _ = record_model
    changes = ({'rrsets': []}, {'rrsets': []}, False)
    with patch.object(record, 'compare', return_value=changes), patch.object(
            record, 'apply_rrsets') as apply_rrsets, patch.object(
                record, 'auto_ptr') as auto_ptr, patch.object(
                    record, 'update_db_serial') as update_serial:
        result = record.apply('example.org', [])

    assert result['status'] == 'ok'
    apply_rrsets.assert_not_called()
    auto_ptr.assert_called_once_with('example.org', changes[0], changes[1])
    update_serial.assert_called_once_with('example.org')


def test_apply_submits_nonempty_patch_then_runs_follow_up_tasks(record_model):
    record, _, _ = record_model
    changes = ({'rrsets': [{
        'name': 'www.example.org.',
        'type': 'A',
        'ttl': 300,
        'changetype': 'REPLACE',
        'records': [{'content': '192.0.2.1', 'disabled': False}],
        'comments': [],
    }]}, {'rrsets': []}, False)

    with patch.object(record, 'compare', return_value=changes), patch.object(
            record, 'apply_rrsets', return_value={}) as apply_rrsets, \
            patch.object(record, 'auto_ptr') as auto_ptr, patch.object(
                record, 'update_db_serial') as update_serial:
        result = record.apply('example.org', [])

    assert result['status'] == 'ok'
    apply_rrsets.assert_called_once()
    auto_ptr.assert_called_once_with('example.org', changes[0], changes[1])
    update_serial.assert_called_once_with('example.org')


def test_apply_returns_clean_powerdns_error_and_stops(record_model):
    record, _, _ = record_model
    changes = ({'rrsets': [{
        'name': 'www.example.org.', 'type': 'A', 'changetype': 'REPLACE'
    }]}, {'rrsets': []}, False)
    with patch.object(record, 'compare', return_value=changes), patch.object(
            record, 'apply_rrsets', return_value={'error': "Invalid 'rrset'"}), \
            patch.object(record, 'auto_ptr') as auto_ptr, patch.object(
                record, 'update_db_serial') as update_serial:
        result = record.apply('example.org', [])

    assert result == {'status': 'error', 'msg': 'Invalid rrset'}
    auto_ptr.assert_not_called()
    update_serial.assert_not_called()


def test_apply_converts_unexpected_exception_to_safe_error(record_model):
    record, _, _ = record_model
    changes = ({'rrsets': [{'changetype': 'REPLACE'}]}, {'rrsets': []}, False)
    with patch.object(record, 'compare', return_value=changes), patch.object(
            record, 'apply_rrsets', side_effect=RuntimeError('secret')):
        result = record.apply('example.org', [])

    assert result['status'] == 'error'
    assert 'secret' not in result['msg']


def test_auto_ptr_adds_and_deletes_reverse_records(record_model):
    record, settings, _ = record_model
    settings['auto_ptr'] = True
    new = {'rrsets': [{
        'name': 'new.example.org.', 'type': 'A', 'ttl': 300,
        'records': [{'content': '192.0.2.20', 'disabled': False}],
    }, {
        'name': 'ignored.example.org.', 'type': 'TXT', 'ttl': 300,
        'records': [{'content': 'ignored', 'disabled': False}],
    }]}
    deleted = {'rrsets': [{
        'name': 'old.example.org.', 'type': 'A', 'ttl': 300,
        'records': [{'content': '192.0.2.10', 'disabled': False}],
    }]}
    domain = MagicMock()
    domain.get_reverse_domain_name.side_effect = [
        '2.0.192.in-addr.arpa', '2.0.192.in-addr.arpa'
    ]

    with patch('powerdnsadmin.models.record.Domain', return_value=domain), \
            patch.object(record, 'delete', return_value={'status': 'ok'}) as delete, \
            patch.object(record, 'add', return_value={'status': 'ok'}) as add:
        result = record.auto_ptr('example.org', new, deleted)

    assert result['status'] == 'ok'
    assert domain.create_reverse_domain.call_args_list == [
        call('example.org', '2.0.192.in-addr.arpa'),
        call('example.org', '2.0.192.in-addr.arpa'),
    ]
    delete.assert_called_once_with('2.0.192.in-addr.arpa')
    added_payload = add.call_args.args[1]
    assert added_payload['rrsets'][0]['name'] == '20.2.0.192.in-addr.arpa.'
    assert added_payload['rrsets'][0]['records'][0]['content'] == (
        'new.example.org.')


def test_auto_ptr_reports_no_changes_and_errors(record_model):
    record, settings, _ = record_model
    settings['auto_ptr'] = True
    assert record.auto_ptr('example.org', {'rrsets': []}, {'rrsets': []}) == {
        'status': 'ok', 'msg': 'No changes detected. Skipping auto ptr...'
    }

    bad = {'rrsets': [{
        'name': 'bad.example.org.', 'type': 'A', 'ttl': 300,
        'records': [{'content': 'not-an-address', 'disabled': False}],
    }]}
    result = record.auto_ptr('example.org', bad, {'rrsets': []})
    assert result['status'] == 'error'


@pytest.mark.parametrize('domain_setting, expected_status', [
    (MagicMock(value='true'), 'ok'),
    (None, None),
])
def test_auto_ptr_uses_domain_setting_when_globally_disabled(
        record_model, domain_setting, expected_status):
    record, _, _ = record_model
    domain = MagicMock()

    with patch('powerdnsadmin.models.record.Domain') as domain_class, patch(
            'powerdnsadmin.models.record.DomainSetting') as setting_class:
        domain_class.query.filter.return_value.first.return_value = domain
        setting_class.query.filter.return_value.filter.return_value.first.return_value = (
            domain_setting)

        result = record.auto_ptr(
            'example.org', {'rrsets': []}, {'rrsets': []})

    if expected_status is None:
        assert result is None
    else:
        assert result['status'] == expected_status


def test_delete_update_permissions_and_exists(record_model):
    record, _, setting = record_model
    record.name = 'www.example.org'
    record.type = 'A'
    record.data = '192.0.2.1'
    record.ttl = 300
    record.status = False

    with patch('powerdnsadmin.models.record.utils.fetch_json',
               return_value={}) as fetch_json:
        assert record.delete('example.org')['status'] == 'ok'
        assert fetch_json.call_args.kwargs['data']['rrsets'][0] == {
            'name': 'www.example.org.', 'type': 'A',
            'changetype': 'DELETE', 'records': []
        }
        assert record.update('example.org', '192.0.2.2')['status'] == 'ok'
        assert fetch_json.call_args.kwargs['data']['rrsets'][0][
            'records'][0]['content'] == '192.0.2.2'

    assert record.is_allowed_edit() is True
    assert record.is_allowed_delete() is True
    record.type = 'SOA'
    assert record.is_allowed_delete() is False
    setting.return_value.get_records_allow_to_edit.return_value = []
    assert record.is_allowed_edit() is False

    record.name = 'www.example.org'
    record.type = 'A'
    with patch.object(record, 'get_rrsets', return_value=[{
        'name': 'www.example.org.', 'type': 'A', 'ttl': 600,
        'records': [{'content': '192.0.2.9', 'disabled': True}],
    }]):
        assert record.exists('example.org') is True
    assert (record.ttl, record.data, record.status) == (600, '192.0.2.9', True)

    record.name = 'missing.example.org'
    with patch.object(record, 'get_rrsets', return_value=[]):
        assert record.exists('example.org') is False


def test_exists_continues_past_nonmatching_rrsets(record_model):
    record, _, _ = record_model
    record.name = 'www.example.org'
    record.type = 'A'
    rrsets = [{
        'name': 'other.example.org.',
        'type': 'A',
        'ttl': 300,
        'records': [{'content': '192.0.2.1', 'disabled': False}],
    }, {
        'name': 'www.example.org.',
        'type': 'A',
        'ttl': 600,
        'records': [{'content': '192.0.2.2', 'disabled': False}],
    }]

    with patch.object(record, 'get_rrsets', return_value=rrsets):
        assert record.exists('example.org') is True
    assert record.data == '192.0.2.2'


@pytest.mark.parametrize('method', ['delete', 'update'])
def test_single_record_mutations_return_safe_errors(record_model, method):
    record, _, _ = record_model
    record.name = 'www.example.org'
    record.type = 'A'
    record.data = '192.0.2.1'
    record.ttl = 300
    record.status = False
    with patch('powerdnsadmin.models.record.utils.fetch_json',
               side_effect=RuntimeError('unavailable')):
        if method == 'delete':
            result = record.delete('example.org')
        else:
            result = record.update('example.org', '192.0.2.2')
    assert result['status'] == 'error'


def test_update_db_serial_updates_known_domain(record_model):
    record, _, _ = record_model
    domain = MagicMock()
    query = MagicMock()
    query.filter.return_value.first.return_value = domain

    with patch('powerdnsadmin.models.record.utils.fetch_json',
               return_value={'serial': 2026080301}), patch(
                   'powerdnsadmin.models.record.Domain.query', query), patch(
                       'powerdnsadmin.models.record.db.session.commit') as commit:
        result = record.update_db_serial('example.org')

    assert result['status'] is True
    assert domain.serial == 2026080301
    commit.assert_called_once_with()


def test_update_db_serial_reports_unknown_domain(record_model):
    record, _, _ = record_model
    query = MagicMock()
    query.filter.return_value.first.return_value = None
    with patch('powerdnsadmin.models.record.utils.fetch_json',
               return_value={'serial': 2026080301}), patch(
                   'powerdnsadmin.models.record.Domain.query', query):
        result = record.update_db_serial('missing.example.org')
    assert result['status'] is False
