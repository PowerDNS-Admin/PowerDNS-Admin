import json

import pytest
from lxml import html

from powerdnsadmin.models.base import db
from powerdnsadmin.models.domain import Domain
from powerdnsadmin.models.history import History


def test_history_table_renders_null_rrset_comments(
        app, logged_in_admin_client):
    with app.app_context():
        History(
            msg='Apply record changes to zone example.org',
            detail=json.dumps({
                'domain': 'example.org',
                'add_rrsets': [{
                    'name': 'example.org.',
                    'type': 'TXT',
                    'ttl': 60,
                    'records': [{
                        'content': 'challenge',
                        'disabled': False,
                    }],
                    'comments': None,
                }],
                'del_rrsets': [],
            }),
            created_by=app.config['TEST_ADMIN_USER'],
        ).add()

    response = logged_in_admin_client.get(
        '/admin/history_table?domain_changelog_only_checkbox=on')

    assert response.status_code == 200
    assert b'challenge' in response.data


def test_history_table_skips_corrupt_history_detail(
        app, logged_in_admin_client):
    with app.app_context():
        History(
            msg='Corrupt history fixture',
            detail='not-json',
            created_by=app.config['TEST_ADMIN_USER'],
        ).add()

    response = logged_in_admin_client.get('/admin/history_table')

    assert response.status_code == 200


@pytest.mark.parametrize('disabled', ['missing', None])
@pytest.mark.parametrize('change', ['addition', 'edit', 'deletion', 'unchanged'])
def test_history_pages_render_records_without_disabled(
        app, logged_in_admin_client, change, disabled):
    """All history views render stored records with absent or null flags."""
    zone_name = f'history-{change}-{disabled}.example'.lower()
    record_name = f'host.{zone_name}.'
    record_set = {
        'name': record_name,
        'type': 'A',
        'ttl': 300,
        'records': [{'content': '192.0.2.1'}],
    }
    if disabled != 'missing':
        record_set['records'][0]['disabled'] = disabled
    new_record_set = record_set
    if change == 'edit':
        new_record_set = {
            **record_set,
            'records': [{**record_set['records'][0], 'disabled': True}],
        }
    detail = {
        'domain': zone_name,
        'add_rrsets': [new_record_set] if change != 'deletion' else [],
        'del_rrsets': [record_set] if change != 'addition' else [],
    }
    with app.app_context():
        zone = Domain(name=zone_name)
        db.session.add(zone)
        db.session.flush()
        db.session.add(History(
            msg=f'Apply record changes to zone {zone_name}',
            detail=json.dumps(detail),
            domain_id=zone.id,
            created_by=app.config['TEST_ADMIN_USER'],
        ))
        db.session.commit()

    for path in [
        '/admin/history_table?domain_changelog_only_checkbox=on',
        f'/domain/{zone_name}/changelog',
        f'/domain/{zone_name}/changelog/{record_name}/A',
    ]:
        response = logged_in_admin_client.get(path)
        assert response.status_code == 200, path
        document = html.fromstring(response.data)
        name_cells = document.xpath(
            '//td[div[normalize-space(.)=$name]]', name=record_name)
        assert len(name_cells) == 1, path
        name_cell = name_cells[0]
        data_cell = name_cell.xpath('following-sibling::td[3]')[0]
        assert '192.0.2.1' in data_cell.text_content(), path
        status_cell = name_cell.xpath('following-sibling::td[4]')[0]
        statuses = status_cell.xpath('./div')
        expected = ['Activated', 'Disabled'] if change == 'edit' else ['Activated']
        assert [status.text_content().strip() for status in statuses] == expected, path
        expected_classes = (['diff-deletion', 'diff-addition'] if change == 'edit'
                            else [f'diff-{change}'])
        for status, expected_class in zip(statuses, expected_classes, strict=True):
            assert expected_class in status.get('class', '').split(), path
