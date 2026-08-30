from types import SimpleNamespace

import pytest
from sqlalchemy.engine import make_url

from powerdnsadmin.lib.settings import AppSettings

DATABASE_ENV_VARS = AppSettings.DATABASE_URI_COMPONENTS + (
    'SQLALCHEMY_DATABASE_URI',
    'SQLALCHEMY_DATABASE_URI_FILE',
    'DATABASE_PASSWORD_FILE',
    'DATABASE_EXTRA_PARAMS',
)


@pytest.fixture
def clean_database_env(monkeypatch):
    for name in DATABASE_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(name + '_FILE', raising=False)


@pytest.mark.parametrize(('configured_value', 'expected_value'), [
    ('true', True),
    ('false', False),
])
def test_load_environment_converts_server_external_ssl_to_boolean(
        clean_database_env, monkeypatch, configured_value, expected_value):
    monkeypatch.setenv('SERVER_EXTERNAL_SSL', configured_value)
    app = SimpleNamespace(config={
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    })

    AppSettings.load_environment(app)

    assert app.config['SERVER_EXTERNAL_SSL'] is expected_value


@pytest.mark.parametrize(('configured_value', 'expected_value'), [
    ('true', True),
    ('false', False),
])
def test_load_environment_converts_saml_lowercase_urlencoding_to_boolean(
        clean_database_env, monkeypatch, configured_value, expected_value):
    monkeypatch.setenv('SAML_LOWERCASE_URLENCODING', configured_value)
    app = SimpleNamespace(config={
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    })

    AppSettings.load_environment(app)

    assert app.config['SAML_LOWERCASE_URLENCODING'] is expected_value


def test_build_database_uri_encodes_unsafe_password(clean_database_env, monkeypatch):
    monkeypatch.setenv('DATABASE_DRIVER', 'mysql')
    monkeypatch.setenv('DATABASE_USER', 'pda')
    monkeypatch.setenv('DATABASE_PASSWORD', 'p@ss,word#1')
    monkeypatch.setenv('DATABASE_HOST', 'mysql')
    monkeypatch.setenv('DATABASE_PORT', '3306')
    monkeypatch.setenv('DATABASE_NAME', 'pda')

    assert AppSettings.build_database_uri_from_environment() == (
        'mysql://pda:p%40ss%2Cword%231@mysql:3306/pda')


def test_build_database_uri_supports_postgres_and_ipv6(clean_database_env, monkeypatch):
    monkeypatch.setenv('DATABASE_DRIVER', 'postgres')
    monkeypatch.setenv('DATABASE_USER', 'pda')
    monkeypatch.setenv('DATABASE_PASSWORD', 'changeme')
    monkeypatch.setenv('DATABASE_HOST', '2001:db8::1')
    monkeypatch.setenv('DATABASE_NAME', 'powerdnsadmin')

    assert AppSettings.build_database_uri_from_environment() == (
        'postgresql://pda:changeme@[2001:db8::1]/powerdnsadmin')


def test_build_database_uri_reads_password_file(
        clean_database_env, monkeypatch, tmp_path):
    secret = tmp_path / 'db_password'
    secret.write_text('p@ss\n')
    monkeypatch.setenv('DATABASE_USER', 'pda')
    monkeypatch.setenv('DATABASE_PASSWORD_FILE', str(secret))
    monkeypatch.setenv('DATABASE_HOST', 'mysql')
    monkeypatch.setenv('DATABASE_NAME', 'pda')

    assert AppSettings.build_database_uri_from_environment() == (
        'mysql://pda:p%40ss@mysql/pda')


def test_build_database_uri_preserves_password_whitespace(
        clean_database_env, monkeypatch):
    monkeypatch.setenv('DATABASE_USER', 'pda')
    monkeypatch.setenv('DATABASE_PASSWORD', ' pass ')
    monkeypatch.setenv('DATABASE_HOST', 'mysql')
    monkeypatch.setenv('DATABASE_NAME', 'pda')

    database_uri = AppSettings.build_database_uri_from_environment()

    assert database_uri == 'mysql://pda:%20pass%20@mysql/pda'
    assert make_url(database_uri).password == ' pass '


def test_build_database_uri_preserves_empty_password(
        clean_database_env, monkeypatch):
    monkeypatch.setenv('DATABASE_USER', 'pda')
    monkeypatch.setenv('DATABASE_PASSWORD', '')
    monkeypatch.setenv('DATABASE_HOST', 'mysql')
    monkeypatch.setenv('DATABASE_NAME', 'pda')

    assert AppSettings.build_database_uri_from_environment() == (
        'mysql://pda:@mysql/pda')


def test_load_environment_builds_uri_from_database_parts(
        clean_database_env, monkeypatch):
    monkeypatch.setenv('DATABASE_USER', 'pda')
    monkeypatch.setenv('DATABASE_PASSWORD', 'p@ss')
    monkeypatch.setenv('DATABASE_HOST', 'mysql')
    monkeypatch.setenv('DATABASE_NAME', 'pda')
    app = SimpleNamespace(config={})

    AppSettings.load_environment(app)

    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'mysql://pda:p%40ss@mysql/pda'


def test_load_environment_prefers_explicit_sqlalchemy_uri(
        clean_database_env, monkeypatch):
    monkeypatch.setenv(
        'SQLALCHEMY_DATABASE_URI', 'mysql://pda:encoded%40pass@mysql/pda')
    monkeypatch.setenv('DATABASE_USER', 'ignored')
    monkeypatch.setenv('DATABASE_PASSWORD', 'ignored')
    monkeypatch.setenv('DATABASE_HOST', 'ignored')
    monkeypatch.setenv('DATABASE_NAME', 'ignored')
    app = SimpleNamespace(config={})

    AppSettings.load_environment(app)

    assert app.config['SQLALCHEMY_DATABASE_URI'] == (
        'mysql://pda:encoded%40pass@mysql/pda')


def test_load_environment_rejects_empty_explicit_sqlalchemy_uri(
        clean_database_env, monkeypatch):
    monkeypatch.setenv('SQLALCHEMY_DATABASE_URI', '')

    with pytest.raises(ValueError, match='cannot be empty'):
        AppSettings.load_environment(SimpleNamespace(config={}))


def test_load_environment_requires_database_configuration(
        clean_database_env):
    with pytest.raises(ValueError, match='Database configuration is required'):
        AppSettings.load_environment(SimpleNamespace(config={}))


def test_load_environment_preserves_database_uri_from_config_file(
        clean_database_env):
    app = SimpleNamespace(config={
        'SQLALCHEMY_DATABASE_URI': 'sqlite:////srv/powerdns-admin.db',
    })

    AppSettings.load_environment(app)

    assert app.config['SQLALCHEMY_DATABASE_URI'] == (
        'sqlite:////srv/powerdns-admin.db')


def test_build_database_uri_requires_host_and_name(clean_database_env, monkeypatch):
    monkeypatch.setenv('DATABASE_PASSWORD', 'p@ss')

    with pytest.raises(ValueError, match='DATABASE_NAME is required'):
        AppSettings.build_database_uri_from_environment()


def test_build_database_uri_sqlite_absolute_path(clean_database_env, monkeypatch):
    monkeypatch.setenv('DATABASE_DRIVER', 'sqlite')
    monkeypatch.setenv('DATABASE_NAME', '/data/powerdns-admin.db')

    assert AppSettings.build_database_uri_from_environment() == (
        'sqlite:////data/powerdns-admin.db')


@pytest.mark.parametrize('port', ['not-a-port', '0', '65536'])
def test_build_database_uri_rejects_invalid_port(
        clean_database_env, monkeypatch, port):
    monkeypatch.setenv('DATABASE_HOST', 'mysql')
    monkeypatch.setenv('DATABASE_PORT', port)
    monkeypatch.setenv('DATABASE_NAME', 'pda')

    with pytest.raises(ValueError, match='DATABASE_PORT'):
        AppSettings.build_database_uri_from_environment()


def test_build_database_uri_appends_extra_params(clean_database_env, monkeypatch):
    monkeypatch.setenv('DATABASE_USER', 'pda')
    monkeypatch.setenv('DATABASE_PASSWORD', 'changeme')
    monkeypatch.setenv('DATABASE_HOST', 'mysql')
    monkeypatch.setenv('DATABASE_NAME', 'pda')
    monkeypatch.setenv(
        'DATABASE_EXTRA_PARAMS', '?ssl=true&ssl_ca=/etc/ssl/certs/ca.pem')

    assert AppSettings.build_database_uri_from_environment() == (
        'mysql://pda:changeme@mysql/pda?ssl=true&ssl_ca=/etc/ssl/certs/ca.pem')


def test_build_database_uri_preserves_extra_params(
        clean_database_env, monkeypatch):
    monkeypatch.setenv('DATABASE_USER', 'pda')
    monkeypatch.setenv('DATABASE_PASSWORD', 'changeme')
    monkeypatch.setenv('DATABASE_HOST', 'mysql')
    monkeypatch.setenv('DATABASE_NAME', 'pda')
    monkeypatch.setenv('DATABASE_EXTRA_PARAMS', '?ssl&driver_flag=a%2Fb')

    assert AppSettings.build_database_uri_from_environment() == (
        'mysql://pda:changeme@mysql/pda?ssl&driver_flag=a%2Fb')


def test_build_database_uri_rejects_extra_params_alone(
        clean_database_env, monkeypatch):
    monkeypatch.setenv('DATABASE_EXTRA_PARAMS', 'ssl=true')

    with pytest.raises(ValueError, match='DATABASE_NAME is required'):
        AppSettings.build_database_uri_from_environment()
