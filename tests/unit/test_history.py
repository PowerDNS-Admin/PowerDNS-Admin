import json
from types import SimpleNamespace

import pytest

from powerdnsadmin.lib.history import (
    get_records,
    normalize_history_detail,
    normalize_rrset,
)
from powerdnsadmin.routes.admin import (
    extract_changelogs_from_history,
    HistoryRecordEntry,
)


def rrset(records=None, comments='missing'):
    result = {
        'name': 'example.test.',
        'type': 'TXT',
        'ttl': 60,
    }
    if records is not None:
        result['records'] = records
    if comments != 'missing':
        result['comments'] = comments
    return result


@pytest.mark.parametrize('comments, expected', [
    (None, [None]),
    ([], [None]),
    ([{'content': 'foo'}], ['foo']),
    ([{'content': 'foo'}, {'content': 'bar'}], ['foo']),
    ([{'content': 'foo'}, {'content': 'bar'}, {'content': 'baz'}], ['foo']),
    ([None], [None]),
    ('missing', [None]),
])
def test_get_records_normalizes_comments(comments, expected):
    records = get_records(rrset([{'content': 'foo', 'disabled': False}], comments))

    assert records == [{
        'content': 'foo',
        'disabled': False,
        'comment': expected[0],
    }]


@pytest.mark.parametrize('value', [None, {}, {'records': []}])
def test_get_records_handles_empty_rrsets(value):
    assert get_records(value) == []


def test_get_records_pairs_multiple_records_by_position():
    records = get_records(rrset([
         {'content': 'foo', 'disabled': False},
         {'content': 'bar', 'disabled': True},
    ], [{'content': 'foo-comment'}, {'content': 'bar-comment'}]))

    assert [record['comment'] for record in records] == [
         'foo-comment', 'bar-comment']


@pytest.mark.parametrize('records', ['invalid', [None], [1]])
def test_get_records_skips_invalid_records(records):
    assert get_records(rrset(records)) == []


def test_get_records_preserves_comment_index_after_invalid_record():
       records = get_records(rrset([
           None,
           {'content': 'bar', 'disabled': False},
       ], [{'content': 'ignored'}, {'content': 'bar-comment'}]))

       assert records == [{
           'content': 'bar',
           'disabled': False,
           'comment': 'bar-comment',
       }]


def test_normalize_rrset_does_not_mutate_input():
    original = rrset([{'content': 'foo'}], None)

    normalize_rrset(original)

    assert original['comments'] is None


def test_normalize_rrset_treats_non_list_comments_as_empty():
    assert normalize_rrset(
        rrset([{'content': 'foo'}], {'content': 'foo'})
    )['comments'] == []


def test_normalize_history_detail_normalizes_both_rrset_collections():
    detail = normalize_history_detail({
        'add_rrsets': [rrset([{'content': 'foo'}], None)],
        'del_rrsets': None,
    })

    assert detail['add_rrsets'][0]['comments'] == []
    assert detail['del_rrsets'] == []


def test_extract_changelogs_normalizes_null_comments():
    detail = {
        'add_rrsets': [rrset([{'content': 'challenge', 'disabled': False}], None)],
        'del_rrsets': [],
    }
    history = SimpleNamespace(detail=json.dumps(detail))

    changes = extract_changelogs_from_history([history])

    assert changes[0].add_rrset['comments'] == []
    assert changes[0].changeSet == [
        (None, {
            'disabled': False,
            'content': 'challenge',
            'comment': None,
        }, 'addition')
    ]


def test_extract_changelogs_processes_legacy_delete_only_detail():
    detail = {
        'del_rrsets': [rrset([{'content': 'old', 'disabled': False}], None)],
    }
    history = SimpleNamespace(detail=json.dumps(detail))

    changes = extract_changelogs_from_history([history])

    assert changes[0].del_rrset['comments'] == []
    assert changes[0].changeSet == [
        ({'disabled': False, 'content': 'old', 'comment': None}, None, 'deletion')
    ]


def test_extract_changelogs_skips_corrupt_history_detail(app):
    history = SimpleNamespace(id=42, detail='not-json')

    with app.app_context():
         assert extract_changelogs_from_history([history]) == []


def test_history_record_entry_normalizes_nullable_rrsets():
    history = SimpleNamespace(created_on=None, created_by=None)
    add_rrset = rrset([{'content': 'challenge', 'disabled': False}], None)

    entry = HistoryRecordEntry(history, {}, add_rrset, '+')

    assert entry.add_rrset['comments'] == []
