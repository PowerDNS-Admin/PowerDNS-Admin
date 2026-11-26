from base64 import b64encode
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from flask import Flask, g
from werkzeug.exceptions import BadGateway, Forbidden, NotFound

from powerdnsadmin.lib import zone_export
from powerdnsadmin.lib.errors import NotEnoughPrivileges
from powerdnsadmin.routes import api, domain


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


@pytest.mark.parametrize(('role', 'enabled', 'allowed'), [
    ('Administrator', False, True), ('Operator', False, True),
    ('User', False, False), ('User', True, True),
    ('Unknown', True, False),
])
def test_export_permission(monkeypatch, role, enabled, allowed):
    monkeypatch.setattr(zone_export, 'Setting', lambda: SimpleNamespace(
        get=lambda name: enabled))
    assert bool(zone_export.export_allowed(role)) is allowed


def test_fetch_native_bind_export(app, monkeypatch):
    values = {'pdns_api_url': 'http://pdns:8081', 'pdns_api_key': 'secret',
              'pdns_api_timeout': 5, 'verify_ssl_connections': True}
    monkeypatch.setattr(zone_export, 'Setting', lambda: SimpleNamespace(
        get=values.get))
    monkeypatch.setattr(zone_export.utils, 'pdns_api_extended_uri',
                        lambda: '/api/v1')
    content = 'example.org. 300 IN TXT "<script> & escaped"\n'
    fetch = MagicMock(return_value={'zone': content})
    monkeypatch.setattr(zone_export.utils, 'fetch_json', fetch)
    with app.app_context():
        assert zone_export.export_zone('example.org') == content
    assert fetch.call_args.args[0] == (
        'http://pdns:8081/api/v1/servers/localhost/zones/example.org./export')
    assert fetch.call_args.kwargs['timeout'] == 5
    assert fetch.call_args.kwargs['verify'] is True


@pytest.mark.parametrize('result', [{}, {'zone': None}, [], {'error': 'failed'}])
def test_invalid_export_is_bad_gateway(app, monkeypatch, result):
    monkeypatch.setattr(zone_export, 'Setting', lambda: SimpleNamespace(
        get=lambda name: 5 if name == 'pdns_api_timeout' else 'http://pdns'))
    monkeypatch.setattr(zone_export.utils, 'pdns_api_extended_uri',
                        lambda: '/api/v1')
    monkeypatch.setattr(zone_export.utils, 'fetch_json', lambda *a, **kw: result)
    with app.app_context(), pytest.raises(BadGateway):
        zone_export.export_zone('example.org')


def test_upstream_failure_is_bad_gateway(app, monkeypatch):
    monkeypatch.setattr(zone_export, 'Setting', lambda: SimpleNamespace(
        get=lambda name: 5 if name == 'pdns_api_timeout' else 'http://pdns'))
    monkeypatch.setattr(zone_export.utils, 'pdns_api_extended_uri',
                        lambda: '/api/v1')
    monkeypatch.setattr(zone_export.utils, 'fetch_json',
                        MagicMock(side_effect=RuntimeError('unavailable')))
    with app.app_context(), pytest.raises(BadGateway):
        zone_export.export_zone('example.org')


def test_download(app):
    with app.test_request_context():
        response = zone_export.zone_download('example.org.', 'zone text\n')
        response.direct_passthrough = False
        assert response.get_data() == b'zone text\n'
        assert response.mimetype == 'text/plain'
        assert 'example.org.zone' in response.headers['Content-Disposition']
        assert response.headers['Cache-Control'] == 'no-store'


@pytest.mark.parametrize('role', ['User', 'Operator', 'Administrator'])
def test_api_export_enforces_permission(app, monkeypatch, role):
    monkeypatch.setattr(api, 'export_allowed', lambda value: value != 'User')
    fetch = MagicMock(return_value='zone text\n')
    monkeypatch.setattr(api, 'export_zone', fetch)
    with app.test_request_context():
        g.apikey = SimpleNamespace(role=SimpleNamespace(name=role))
        handler = api.api_zone_export.__wrapped__.__wrapped__
        if role == 'User':
            with pytest.raises(NotEnoughPrivileges):
                handler('localhost', 'example.org.')
            fetch.assert_not_called()
        else:
            response = handler('localhost', 'example.org.')
            assert response.status_code == 200
            fetch.assert_called_once_with('example.org.', 'localhost')


def test_ui_export_denies_user(app, monkeypatch):
    monkeypatch.setattr(domain, 'current_user', SimpleNamespace(
        role=SimpleNamespace(name='User')))
    monkeypatch.setattr(domain, 'export_allowed', lambda role: False)
    with app.test_request_context(), pytest.raises(Forbidden):
        domain.export.__wrapped__.__wrapped__('example.org')


def test_ui_export_checks_zone_exists(app, monkeypatch):
    monkeypatch.setattr(domain, 'current_user', SimpleNamespace(
        role=SimpleNamespace(name='Operator')))
    monkeypatch.setattr(domain, 'Domain', SimpleNamespace(
        name='name', query=MagicMock()))
    domain.Domain.query.filter.return_value.first.return_value = None
    with app.test_request_context(), pytest.raises(NotFound):
        domain.export.__wrapped__.__wrapped__('example.org')


@pytest.mark.parametrize('suffix', ['export', 'export/'])
@pytest.mark.parametrize(('role', 'enabled', 'assigned', 'expected'), [
    ('User', False, True, 401), ('User', True, True, 200),
    ('User', True, False, 403), ('Operator', False, False, 200),
    ('Administrator', False, False, 200),
])
def test_api_export_auth_and_zone_scope(app, monkeypatch, role, enabled,
                                       assigned, expected, suffix):
    from powerdnsadmin import decorators

    key = SimpleNamespace(
        role=SimpleNamespace(name=role), accounts=[],
        domains=[SimpleNamespace(name='example.org')] if assigned else [])
    key_model = MagicMock()
    key_model.return_value.is_validate.return_value = key
    monkeypatch.setattr(decorators, 'ApiKey', key_model)
    monkeypatch.setattr(zone_export, 'Setting', lambda: SimpleNamespace(
        get=lambda name: enabled))
    monkeypatch.setattr(api, 'export_zone', lambda *args: 'example.org. IN SOA\n')
    monkeypatch.setattr(api, 'Setting', lambda: SimpleNamespace(
        get=lambda name: False))
    app.register_blueprint(api.api_bp)
    response = app.test_client().get(
        f'/api/v1/servers/localhost/zones/example.org./{suffix}',
        headers={'X-API-Key': b64encode(b'test-key').decode('ascii')})
    assert response.status_code == expected
    if expected == 200:
        assert response.data == b'example.org. IN SOA\n'
