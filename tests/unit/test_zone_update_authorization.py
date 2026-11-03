import re
from unittest.mock import patch

import pytest

from powerdnsadmin.models.account import Account
from powerdnsadmin.models.account_user import AccountUser
from powerdnsadmin.models.base import db
from powerdnsadmin.models.domain import Domain
from powerdnsadmin.models.domain_user import DomainUser
from powerdnsadmin.models.user import User


@pytest.fixture(scope='module')
def update_zones(app, initial_data):
    with app.app_context():
        user = User.query.filter_by(username=app.config['TEST_USER']).one()
        account = Account(name='updatetest')
        db.session.add(account)
        db.session.flush()
        own = Domain(name='owned.example', type='Slave')
        inherited = Domain(name='account.example', type='Slave', account_id=account.id)
        victim = Domain(name='victim.example', type='Slave')
        db.session.add_all([own, inherited, victim])
        db.session.flush()
        db.session.add(DomainUser(own.id, user.id))
        db.session.add(AccountUser(account.id, user.id))
        db.session.commit()


@pytest.fixture
def update_client(app, client, update_zones):
    page = client.get('/login')
    token = re.search(rb'name="_csrf_token" value="([^"]+)"', page.data).group(1).decode()
    with app.app_context():
        user_id = User.query.filter_by(username=app.config['TEST_USER']).one().id
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True
    return client, token


def post_update(update_client, zone, payload, csrf=True):
    client, token = update_client
    headers = {'X-CSRFToken': token} if csrf else {}
    return client.post('/domain/' + zone + '/update', json=payload, headers=headers)


@pytest.mark.parametrize('zone', ['owned.example', 'account.example'])
def test_body_cannot_override_authorized_zone(update_client, zone):
    with patch('powerdnsadmin.models.domain.utils.fetch_json',
               return_value={'result': 'queued'}) as fetch:
        response = post_update(update_client, zone, {'domain': 'victim.example'})
    assert response.status_code == 403
    fetch.assert_not_called()


@pytest.mark.parametrize('zone', ['owned.example', 'account.example'])
@pytest.mark.parametrize('legacy_body', [True, False])
def test_update_uses_authorized_url_zone(update_client, zone, legacy_body):
    payload = {'domain': zone} if legacy_body else {}
    with patch('powerdnsadmin.models.domain.utils.fetch_json',
               return_value={'result': 'queued'}) as fetch:
        response = post_update(update_client, zone, payload)
    assert response.status_code == 200
    assert response.json == {'status': 'ok', 'msg': 'queued'}
    fetch.assert_called_once()
    assert fetch.call_args.args[0].endswith('/zones/' + zone + '/axfr-retrieve')
    assert fetch.call_args.kwargs['method'] == 'PUT'


@pytest.mark.parametrize(('zone', 'status'), [
    ('victim.example', 403), ('missing.example', 404),
])
def test_url_zone_access_is_required(update_client, zone, status):
    with patch('powerdnsadmin.models.domain.utils.fetch_json') as fetch:
        response = post_update(update_client, zone, {'domain': 'owned.example'})
    assert response.status_code == status
    fetch.assert_not_called()


@pytest.mark.parametrize('payload', [[], 'victim.example', 1])
def test_update_rejects_non_object_payload(update_client, payload):
    with patch('powerdnsadmin.models.domain.utils.fetch_json') as fetch:
        response = post_update(update_client, 'owned.example', payload)
    assert response.status_code == 400
    fetch.assert_not_called()


def test_update_requires_csrf(update_client):
    with patch('powerdnsadmin.models.domain.utils.fetch_json') as fetch:
        response = post_update(update_client, 'owned.example', {}, csrf=False)
    assert response.status_code == 403
    fetch.assert_not_called()


def test_update_preserves_backend_failure(update_client):
    with patch('powerdnsadmin.models.domain.utils.fetch_json',
               side_effect=RuntimeError('backend unavailable')):
        response = post_update(update_client, 'owned.example', {'domain': 'owned.example'})
    assert response.status_code == 500
    assert response.json['status'] == 'error'
