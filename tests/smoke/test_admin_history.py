import json

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