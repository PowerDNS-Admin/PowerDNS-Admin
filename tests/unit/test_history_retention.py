import json
import re

from powerdnsadmin.models.base import db
from powerdnsadmin.models.domain import Domain
from powerdnsadmin.models.history import History
from powerdnsadmin.models.setting import Setting
from powerdnsadmin.models.user import User
from powerdnsadmin.routes.admin import DetailedHistory


def _csrf_token(response):
    match = re.search(
        rb'name="_csrf_token" value="([^"]+)"',
        response.data,
    )
    assert match is not None
    return match.group(1).decode('utf-8')


def _login(client, app):
    page = client.get('/login')
    response = client.post(
        '/login',
        data={
            'username': app.config['TEST_ADMIN_USER'],
            'password': app.config['TEST_ADMIN_PASSWORD'],
            'auth_method': 'LOCAL',
            '_csrf_token': _csrf_token(page),
        },
    )
    assert response.status_code == 302


def test_activity_page_has_no_clear_control(app, client, initial_data):
    _login(client, app)
    page = client.get('/admin/history')
    body = page.get_data(as_text=True)

    assert page.status_code == 200
    assert 'Activity Search' in body
    assert 'Clear Activity' not in body
    assert 'modal_clear_history' not in body
    assert 'remove all history' not in body.lower()


def test_activity_post_cannot_delete_rows(app, client, initial_data):
    _login(client, app)
    with app.app_context():
        History(
            msg='Retention marker',
            created_by=app.config['TEST_ADMIN_USER'],
        ).add()
        before = History.query.count()

    token_page = client.get('/admin/setting/pdns')
    token = _csrf_token(token_page)
    for path in ('/admin/history', '/admin/history_table'):
        response = client.post(path, data={'_csrf_token': token})
        assert response.status_code == 405

    with app.app_context():
        assert History.query.count() == before
        assert History.query.filter_by(msg='Retention marker').count() == 1


def test_zone_removal_keeps_its_activity(app, initial_data):
    zone_name = 'kept-history.example.com'
    with app.app_context():
        Setting().set('preserve_history', False)
        domain = Domain(name=zone_name, type='NATIVE')
        db.session.add(domain)
        db.session.commit()
        History(
            msg='Update zone {0}'.format(zone_name),
            created_by='admin',
            domain_id=domain.id,
        ).add()

        Domain().delete_domain_from_pdnsadmin(zone_name)

        kept = History.query.filter(
            History.msg == 'Update zone {0}'.format(zone_name)).one()
        assert kept.domain_id is None
        assert Domain.query.filter_by(name=zone_name).count() == 0


def test_disabling_two_factor_records_the_source_address(
        app, client, initial_data):
    target = app.config['TEST_USER']
    with app.app_context():
        account = User.query.filter_by(username=target).one()
        account.otp_secret = 'JBSWY3DPEHPK3PXP'
        db.session.commit()

    _login(client, app)
    token_page = client.get('/admin/setting/pdns')
    response = client.post(
        '/admin/manage-user',
        json={
            'action': 'user_otp_disable',
            'data': target,
            '_csrf_token': _csrf_token(token_page),
        },
        headers={
            'X-CSRFToken': _csrf_token(token_page),
            'X-Forwarded-For': '198.51.100.20, 10.0.0.8',
        },
    )
    assert response.status_code == 200

    with app.app_context():
        account = User.query.filter_by(username=target).one()
        assert account.otp_secret == ''
        row = History.query.filter(
            History.msg.like('Two factor authentication disabled%')).one()
        assert row.msg == (
            'Two factor authentication disabled for user {0} from 198.51.100.20'
            .format(target))
        assert row.created_by == app.config['TEST_ADMIN_USER']
        assert json.loads(row.detail)['ip_address'] == '198.51.100.20'
        detail = DetailedHistory(row, None).detailed_msg
        assert '198.51.100.20' in detail
        assert 'IP Address' in detail


def test_enabling_two_factor_records_the_source_address(
        app, client, initial_data):
    username = app.config['TEST_USER']
    password = app.config['TEST_USER_PASSWORD']
    page = client.get('/login')
    signed_in = client.post(
        '/login',
        data={
            'username': username,
            'password': password,
            'auth_method': 'LOCAL',
            '_csrf_token': _csrf_token(page),
        },
    )
    assert signed_in.status_code == 302

    profile = client.get('/user/profile')
    response = client.post(
        '/user/profile',
        json={
            'action': 'enable_otp',
            'data': {'enable_otp': True, 'otp_token': ''},
            '_csrf_token': _csrf_token(profile),
        },
        headers={
            'X-CSRFToken': _csrf_token(profile),
            'X-Forwarded-For': '203.0.113.44',
        },
    )
    assert response.status_code == 200

    with app.app_context():
        account = User.query.filter_by(username=username).one()
        assert account.otp_secret
        row = History.query.filter(
            History.msg.like('Two factor authentication enabled%')).one()
        assert row.msg == (
            'Two factor authentication enabled for user {0} from 203.0.113.44'
            .format(username))
        assert row.created_by == username
        assert json.loads(row.detail)['ip_address'] == '203.0.113.44'
        assert '203.0.113.44' in DetailedHistory(row, None).detailed_msg


def test_activity_records_host_and_user_agent(app, client, initial_data):
    with app.test_request_context(
            '/admin/history',
            base_url='http://pda.example',
            headers={'User-Agent': 'activity-browser/1'}):
        History(msg='Host agent marker', created_by='admin').add()

    with app.app_context():
        row = History.query.filter_by(msg='Host agent marker').one()
        assert row.host == 'pda.example'
        assert row.user_agent == 'activity-browser/1'

    _login(client, app)
    page = client.get('/admin/history_table')
    body = page.get_data(as_text=True)
    assert page.status_code == 200
    assert 'Host agent marker' in body
    assert 'pda.example' in body
    assert 'activity-browser/1' in body
