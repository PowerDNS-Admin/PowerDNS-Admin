from types import SimpleNamespace

import pytest
from flask import Flask, g
from werkzeug.exceptions import BadRequest

from powerdnsadmin.lib.errors import DomainAccessForbidden
from powerdnsadmin.lib import helper


class Settings:
    def __init__(self, **values):
        self.values = values

    def get(self, name):
        return self.values[name]


class Response:
    content = b'[]'
    status_code = 200
    headers = {}


@pytest.fixture
def flask_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


def test_forward_request_rejects_dot_segments_and_verifies_tls(
        flask_app, monkeypatch):
    calls = []

    def capture(method, url, headers=None, verify=None, json=None):
        calls.append({'url': url, 'verify': verify})
        return Response()

    monkeypatch.setattr(helper, 'Setting', lambda: Settings(
        pdns_api_url='http://pdns.test/',
        pdns_api_key='backend-key',
        verify_ssl_connections=True,
    ))
    monkeypatch.setattr(helper.requests, 'request', capture)

    with flask_app.test_request_context(
            '/api/v1/servers/localhost/zones/allowed.example/../private.example'):
        with pytest.raises(BadRequest):
            helper.forward_request()
    assert calls == []

    with flask_app.test_request_context(
            '/api/v1/servers/localhost/zones/allowed.example/%2e%2e/private.example'):
        with pytest.raises(BadRequest):
            helper.forward_request()

    with flask_app.test_request_context(
            '/api/v1/servers/localhost/zones/allowed.example/metadata'):
        g.apikey = SimpleNamespace(
            role=SimpleNamespace(name='User'),
            domains=[SimpleNamespace(name='allowed.example')],
            accounts=[],
        )
        helper.forward_request()

    assert calls == [{
        'url': 'http://pdns.test/api/v1/servers/localhost/zones/allowed.example/metadata',
        'verify': True,
    }]

    with flask_app.test_request_context(
            '/api/v1/servers/localhost/zones/private.example/metadata'):
        g.apikey = SimpleNamespace(
            role=SimpleNamespace(name='User'),
            domains=[SimpleNamespace(name='allowed.example')],
            accounts=[],
        )
        with pytest.raises(DomainAccessForbidden):
            helper.forward_request()
