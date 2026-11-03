import pytest
from flask import Flask

from powerdnsadmin.lib.deployment_secrets import (
    PUBLISHED_SALTS,
    PUBLISHED_SECRET_KEYS,
    assert_deployment_secrets,
)


def _app(secret, salt):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = secret
    app.config['SALT'] = salt
    return app


def test_published_secret_and_salt_are_rejected(monkeypatch):
    monkeypatch.delenv('PDA_ALLOW_INSECURE_SECRETS', raising=False)
    app = _app(next(iter(PUBLISHED_SECRET_KEYS)), next(iter(PUBLISHED_SALTS)))

    with pytest.raises(RuntimeError, match='SECRET_KEY and SALT'):
        assert_deployment_secrets(app)


def test_unique_secret_and_salt_are_accepted(monkeypatch):
    monkeypatch.delenv('PDA_ALLOW_INSECURE_SECRETS', raising=False)
    app = _app('deployment-secret-not-from-the-repo',
               '$2b$12$UniqueDeploySaltValue1')

    assert_deployment_secrets(app)


def test_short_secret_and_malformed_salt_are_rejected(monkeypatch):
    monkeypatch.delenv('PDA_ALLOW_INSECURE_SECRETS', raising=False)
    app = _app('abc', 'not-a-salt')

    with pytest.raises(RuntimeError, match='SECRET_KEY and SALT'):
        assert_deployment_secrets(app)


def test_empty_secret_is_rejected(monkeypatch):
    monkeypatch.delenv('PDA_ALLOW_INSECURE_SECRETS', raising=False)
    app = _app('', '$2b$12$UniqueDeploySaltValue1')

    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        assert_deployment_secrets(app)


def test_testing_config_may_keep_published_values(monkeypatch):
    monkeypatch.delenv('PDA_ALLOW_INSECURE_SECRETS', raising=False)
    app = _app(next(iter(PUBLISHED_SECRET_KEYS)), next(iter(PUBLISHED_SALTS)))
    app.config['TESTING'] = True

    assert_deployment_secrets(app)
