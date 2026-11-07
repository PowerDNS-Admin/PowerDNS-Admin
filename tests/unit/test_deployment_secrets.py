import logging

import bcrypt
import pytest
from flask import Flask

from powerdnsadmin.lib.deployment_secrets import (
    PUBLISHED_SECRET_KEYS,
    _salt_rejected,
    assert_deployment_secrets,
)

SHIPPED_SALT = '$2b$12$yLUMTIfl21FKJQpTkRQXCu'
VALID_SALT = bcrypt.gensalt(rounds=4).decode('ascii')


def _app(secret, salt):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = secret
    app.config['SALT'] = salt
    return app


def test_published_secret_is_rejected_with_the_shipped_salt(monkeypatch):
    monkeypatch.delenv('PDA_ALLOW_INSECURE_SECRETS', raising=False)
    app = _app(next(iter(PUBLISHED_SECRET_KEYS)), SHIPPED_SALT)

    with pytest.raises(RuntimeError, match='because SECRET_KEY is') as caught:
        assert_deployment_secrets(app)

    message = str(caught.value)
    assert 'environment variables documentation' in message
    assert 'PDA_ALLOW_INSECURE_SECRETS' not in message


def _warning_messages(app):
    messages = []

    class _Capture(logging.Handler):
        def emit(self, record):
            messages.append(record.getMessage())

    handler = _Capture()
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.WARNING)
    return messages


def test_published_salt_warns_and_starts(monkeypatch):
    monkeypatch.delenv('PDA_ALLOW_INSECURE_SECRETS', raising=False)
    app = _app('deployment-secret-not-from-the-repo', SHIPPED_SALT)
    messages = _warning_messages(app)

    assert_deployment_secrets(app)

    assert any('published in the PowerDNS-Admin repository' in message
               for message in messages)


def test_unique_salt_does_not_warn(monkeypatch):
    monkeypatch.delenv('PDA_ALLOW_INSECURE_SECRETS', raising=False)
    app = _app('deployment-secret-not-from-the-repo',
               VALID_SALT)
    messages = _warning_messages(app)

    assert_deployment_secrets(app)

    assert messages == []


def test_unique_secret_and_salt_are_accepted(monkeypatch):
    monkeypatch.delenv('PDA_ALLOW_INSECURE_SECRETS', raising=False)
    app = _app('deployment-secret-not-from-the-repo',
               VALID_SALT)

    assert_deployment_secrets(app)


def test_short_secret_and_malformed_salt_are_rejected(monkeypatch):
    monkeypatch.delenv('PDA_ALLOW_INSECURE_SECRETS', raising=False)
    app = _app('abc', 'not-a-salt')

    with pytest.raises(RuntimeError, match='SECRET_KEY and SALT'):
        assert_deployment_secrets(app)


def test_published_secret_with_trailing_newline_is_rejected(monkeypatch):
    monkeypatch.delenv('PDA_ALLOW_INSECURE_SECRETS', raising=False)
    app = _app('e951e5a1f4b94151b360f47edf596dd2\n',
               VALID_SALT)

    with pytest.raises(RuntimeError, match='because SECRET_KEY is'):
        assert_deployment_secrets(app)


def test_secret_length_ignores_surrounding_whitespace(monkeypatch):
    monkeypatch.delenv('PDA_ALLOW_INSECURE_SECRETS', raising=False)
    app = _app(('a' * 31) + '\n', VALID_SALT)

    with pytest.raises(RuntimeError, match='because SECRET_KEY is'):
        assert_deployment_secrets(app)


def test_empty_secret_is_rejected(monkeypatch):
    monkeypatch.delenv('PDA_ALLOW_INSECURE_SECRETS', raising=False)
    app = _app('', VALID_SALT)

    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        assert_deployment_secrets(app)


def test_testing_config_may_keep_published_values(monkeypatch):
    monkeypatch.delenv('PDA_ALLOW_INSECURE_SECRETS', raising=False)
    app = _app(next(iter(PUBLISHED_SECRET_KEYS)), SHIPPED_SALT)
    app.config['TESTING'] = True

    assert_deployment_secrets(app)


@pytest.mark.parametrize('salt', [
    None,
    b'$2b$12$yLUMTIfl21FKJQpTkRQXCu',
    '',
    '$2b$00$yLUMTIfl21FKJQpTkRQXCu',
    '$2b$99$yLUMTIfl21FKJQpTkRQXCu',
    '$2b$xx$yLUMTIfl21FKJQpTkRQXCu',
    '$2b$12$UniqueDeploySaltValue1',
    '$2b$12$abcdefghijklmnopqrstuv',
    '$2z$12$yLUMTIfl21FKJQpTkRQXCu',
    '$2b$12$yLUMTIfl21FKJQpTkRQXCé',
    SHIPPED_SALT + '\n',
    SHIPPED_SALT + 'a' * 31,
])
def test_bcrypt_rejects_unusable_salt_at_startup(monkeypatch, salt):
    monkeypatch.delenv('PDA_ALLOW_INSECURE_SECRETS', raising=False)
    app = _app('deployment-secret-not-from-the-repo', salt)

    with pytest.raises(RuntimeError, match='because SALT is'):
        assert_deployment_secrets(app)


@pytest.mark.parametrize('version', ['2a', '2b', '2x', '2y'])
def test_bcrypt_accepts_supported_salt_versions(version):
    salt = '${}$04${}'.format(version, VALID_SALT[7:])

    assert not _salt_rejected(salt)


def test_salt_validation_does_not_hash_at_the_configured_cost(monkeypatch):
    hashpw = bcrypt.hashpw
    calls = []

    def bounded_hashpw(password, salt):
        assert salt[4:6] == b'04'
        calls.append(salt)
        return hashpw(password, salt)

    monkeypatch.setattr(bcrypt, 'hashpw', bounded_hashpw)
    salt = '$2b$31$' + VALID_SALT[7:]

    assert not _salt_rejected(salt)
    assert calls == [('$2b$04$' + VALID_SALT[7:]).encode('ascii')]
