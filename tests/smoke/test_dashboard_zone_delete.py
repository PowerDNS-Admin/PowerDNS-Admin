from unittest.mock import patch

import pytest
from lxml import html

from powerdnsadmin.models.base import db
from powerdnsadmin.models.domain import Domain
from powerdnsadmin.models.domain_user import DomainUser
from powerdnsadmin.models.setting import Setting
from powerdnsadmin.models.user import User


@pytest.fixture
def deletion_zone(app, initial_data):
    with app.app_context():
        zone = Domain(name='xn--bcher-kva.example')
        db.session.add(zone)
        db.session.commit()
        zone_id = zone.id
    yield zone_id
    with app.app_context():
        DomainUser.query.filter_by(domain_id=zone_id).delete()
        Domain.query.filter_by(id=zone_id).delete()
        db.session.commit()


def authenticate(app, client, username):
    with app.app_context():
        user_id = User.query.filter_by(username=username).one().id
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def deletion_form(client, dashboard='/dashboard/'):
    with patch.object(Domain, 'update'):
        response = client.get(dashboard)
    assert response.status_code == 200
    document = html.fromstring(response.data)
    form = document.get_element_by_id('dashboard-zone-delete-form')
    assert form.get('action') == '/domain/remove'
    return document, form.xpath('.//input[@name="_csrf_token"]/@value')[0]


@pytest.mark.parametrize('dashboard', ['/dashboard/', '/dashboard/v2/'])
def test_dashboard_can_delete_selected_zone(
        app, client, deletion_zone, dashboard):
    authenticate(app, client, app.config['TEST_ADMIN_USER'])
    document, token = deletion_form(client, dashboard)
    assert len(document.xpath('//script[contains(@src,"dashboard-zone-delete.js")]')) == 1
    if dashboard == '/dashboard/':
        # Classic rows are rendered separately for server-side DataTables.
        with app.test_request_context():
            template = app.jinja_env.get_template('dashboard_domain.html')
            module = template.make_module({
                'current_user': User.query.filter_by(
                    username=app.config['TEST_ADMIN_USER']).one(),
                'allow_user_remove_domain': True,
                'allow_user_view_history': True,
            })
            zone = Domain.query.filter_by(id=deletion_zone).one()
            button = html.fromstring(str(module.actions(zone))).xpath(
                '//button[contains(@class,"dashboard-remove-zone")]')[0]
        assert button.get('data-domain') == 'xn--bcher-kva.example'
        assert button.get('onclick') is None

    with patch.object(Domain, 'delete', return_value={'status': 'ok'}) as delete:
        response = client.post('/domain/remove', data={
            '_csrf_token': token, 'domainid': 'xn--bcher-kva.example',
        }, headers={'Accept': 'application/json'})
    assert response.status_code == 200
    assert response.json == {'status': 'ok'}
    delete.assert_called_once_with('xn--bcher-kva.example')


@pytest.mark.parametrize('allowed,associated,expected', [
    (True, True, 200),
    (True, False, 403),
    (False, True, 403),
])
def test_dashboard_deletion_checks_user_permissions(
        app, client, deletion_zone, allowed, associated, expected):
    with app.app_context():
        setting = Setting.query.filter_by(name='allow_user_remove_domain').one()
        previous = setting.value
        setting.value = str(allowed)
        user = User.query.filter_by(username=app.config['TEST_USER']).one()
        if associated:
            db.session.add(DomainUser(deletion_zone, user.id))
        db.session.commit()
    try:
        authenticate(app, client, app.config['TEST_USER'])
        _, token = deletion_form(client)
        with patch.object(Domain, 'delete', return_value={'status': 'ok'}) as delete:
            response = client.post('/domain/remove', data={
                '_csrf_token': token, 'domainid': 'xn--bcher-kva.example',
            }, headers={'Accept': 'application/json'})
        assert response.status_code == expected
        assert delete.call_count == int(expected == 200)
    finally:
        with app.app_context():
            Setting.query.filter_by(name='allow_user_remove_domain').update(
                {'value': previous})
            db.session.commit()


def test_dashboard_deletion_requires_csrf_token(app, client, deletion_zone):
    authenticate(app, client, app.config['TEST_ADMIN_USER'])
    with patch.object(Domain, 'delete') as delete:
        response = client.post('/domain/remove', data={
            'domainid': 'xn--bcher-kva.example',
        }, headers={'Accept': 'application/json'})
    assert response.status_code == 403
    delete.assert_not_called()


def test_dashboard_deletion_reports_backend_failure(app, client, deletion_zone):
    authenticate(app, client, app.config['TEST_ADMIN_USER'])
    _, token = deletion_form(client)
    with patch.object(Domain, 'delete', return_value={'status': 'error'}):
        response = client.post('/domain/remove', data={
            '_csrf_token': token, 'domainid': 'xn--bcher-kva.example',
        }, headers={'Accept': 'application/json'})
    assert response.status_code == 500
