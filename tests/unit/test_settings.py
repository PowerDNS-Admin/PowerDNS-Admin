from types import SimpleNamespace

import pytest

from powerdnsadmin.lib.settings import AppSettings


@pytest.mark.parametrize(('configured_value', 'expected_value'), [
    ('true', True),
    ('false', False),
])
def test_load_environment_converts_server_external_ssl_to_boolean(
        monkeypatch, configured_value, expected_value):
    monkeypatch.setenv('SERVER_EXTERNAL_SSL', configured_value)
    app = SimpleNamespace(config={})

    AppSettings.load_environment(app)

    assert app.config['SERVER_EXTERNAL_SSL'] is expected_value
