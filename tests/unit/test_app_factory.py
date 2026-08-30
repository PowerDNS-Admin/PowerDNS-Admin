import logging
import os
import sys
from types import ModuleType, SimpleNamespace

import pytest

import powerdnsadmin
import powerdnsadmin.models as models
import powerdnsadmin.routes as routes
import powerdnsadmin.services as services
from powerdnsadmin.assets import assets
from powerdnsadmin.lib.settings import AppSettings
import powerdnsadmin.models.setting as setting_module


@pytest.fixture
def isolated_app_factory(monkeypatch):
    """Replace extension setup so app-factory tests need no services."""
    calls = SimpleNamespace(
        models=[], sessions=[], mail=[], assets=[], routes=[], services=[],
        environment=[], settings=[], sslify=[])

    monkeypatch.setattr(models, 'init_app', calls.models.append)
    monkeypatch.setattr(routes, 'init_app', calls.routes.append)
    monkeypatch.setattr(services, 'init_app', calls.services.append)
    monkeypatch.setattr(assets, 'init_app', calls.assets.append)
    monkeypatch.setattr(powerdnsadmin, 'Session',
                        lambda app: calls.sessions.append(app))

    class FakeMail:
        def __init__(self, app):
            calls.mail.append(app)

    class FakeSetting:
        def __init__(self):
            calls.settings.append(self)

        def get(self, name):
            return 'Test Site' if name == 'site_name' else None

    monkeypatch.setattr(powerdnsadmin, 'Mail', FakeMail)
    monkeypatch.setattr(setting_module, 'Setting', FakeSetting)
    monkeypatch.setattr(AppSettings, 'load_environment',
                        lambda app: calls.environment.append(app))
    monkeypatch.setattr(powerdnsadmin.utils, 'read_app_version',
                        lambda root_path: 'test-version')

    for variable in (
            'FLASK_CONF', 'FLASK_DEBUG', 'GUNICORN_LOGLEVEL',
            'PDNS_ADMIN_LOG_LEVEL', 'POWERDNSADMIN_ASSETS_PREBUILT',
            'SESSION_TYPE'):
        monkeypatch.delenv(variable, raising=False)

    return calls


def test_create_app_initializes_components_filters_and_context(
        monkeypatch, isolated_app_factory):
    calls = isolated_app_factory
    monkeypatch.setenv('PDNS_ADMIN_LOG_LEVEL', 'info')
    monkeypatch.setenv('POWERDNSADMIN_ASSETS_PREBUILT', '1')

    app = powerdnsadmin.create_app({
        'CUSTOM_SETTING': 'configured',
        'SESSION_TYPE': None,
    })

    assert app.config['CUSTOM_SETTING'] == 'configured'
    assert app.config['APP_VERSION'] == 'test-version'
    assert app.config['ASSETS_AUTO_BUILD'] is False
    assert logging.getLogger('sqlalchemy.pool').level != logging.DEBUG
    assert calls.models == [app]
    assert calls.sessions == [app]
    assert calls.mail == [app]
    assert calls.assets == [app]
    assert calls.routes == [app]
    assert calls.services == [app]
    assert calls.environment == [app]

    assert app.jinja_env.filters == {
        **app.jinja_env.filters,
        'display_record_name': powerdnsadmin.utils.display_record_name,
        'display_master_name': powerdnsadmin.utils.display_master_name,
        'display_second_to_time': powerdnsadmin.utils.display_time,
        'display_setting_state': powerdnsadmin.utils.display_setting_state,
        'pretty_domain_name': powerdnsadmin.utils.pretty_domain_name,
        'format_datetime_local': powerdnsadmin.utils.format_datetime,
        'format_zone_type': powerdnsadmin.utils.format_zone_type,
    }

    context = {}
    app.update_template_context(context)
    assert context['SITE_NAME'] == 'Test Site'
    assert isinstance(context['SETTING'], setting_module.Setting)
    assert context['APP_VERSION'] == 'test-version'


def test_create_app_loads_environment_and_python_configs(
        tmp_path, monkeypatch, isolated_app_factory):
    calls = isolated_app_factory
    environment_config = tmp_path / 'environment.py'
    environment_config.write_text('FROM_ENVIRONMENT = True\n')
    app_config = tmp_path / 'application.py'
    app_config.write_text('FROM_APPLICATION = True\nHSTS_ENABLED = True\n')

    monkeypatch.setenv('FLASK_CONF', str(environment_config))
    monkeypatch.setenv('SESSION_TYPE', 'sqlalchemy')
    monkeypatch.setenv('GUNICORN_LOGLEVEL', 'info')

    pool_logger = logging.Logger('sqlalchemy.pool')
    gunicorn_logger = logging.Logger('gunicorn.error', logging.INFO)
    gunicorn_logger.handlers = [logging.NullHandler()]
    original_get_logger = logging.getLogger

    def get_logger(name=None):
        if name == 'sqlalchemy.pool':
            return pool_logger
        if name == 'gunicorn.error':
            return gunicorn_logger
        return original_get_logger(name)

    monkeypatch.setattr(logging, 'getLogger', get_logger)

    sslify_module = ModuleType('flask_sslify')
    sslify_module.SSLify = lambda app: calls.sslify.append(app)
    monkeypatch.setitem(sys.modules, 'flask_sslify', sslify_module)

    app = powerdnsadmin.create_app(str(app_config))

    assert app.config['FROM_ENVIRONMENT'] is True
    assert app.config['FROM_APPLICATION'] is True
    assert app.config['SESSION_TYPE'] == 'sqlalchemy'
    assert app.config['SESSION_SQLALCHEMY'] is models.db
    assert pool_logger.level != logging.DEBUG
    assert app.logger.handlers == gunicorn_logger.handlers
    assert app.logger.level == gunicorn_logger.level
    assert calls.sslify == [app]


def test_create_app_enables_sqlalchemy_pool_debug_when_log_level_is_debug(
        monkeypatch, isolated_app_factory):
    monkeypatch.setenv('PDNS_ADMIN_LOG_LEVEL', 'DEBUG')

    pool_logger = logging.Logger('sqlalchemy.pool')
    original_get_logger = logging.getLogger

    def get_logger(name=None):
        if name == 'sqlalchemy.pool':
            return pool_logger
        return original_get_logger(name)

    monkeypatch.setattr(logging, 'getLogger', get_logger)

    powerdnsadmin.create_app({'SESSION_TYPE': None})

    assert pool_logger.level == logging.DEBUG


def test_create_app_enables_sqlalchemy_pool_debug_when_flask_debug(
        monkeypatch, isolated_app_factory):
    monkeypatch.setenv('FLASK_DEBUG', '1')

    pool_logger = logging.Logger('sqlalchemy.pool')
    original_get_logger = logging.getLogger

    def get_logger(name=None):
        if name == 'sqlalchemy.pool':
            return pool_logger
        return original_get_logger(name)

    monkeypatch.setattr(logging, 'getLogger', get_logger)

    powerdnsadmin.create_app({'SESSION_TYPE': None})

    assert pool_logger.level == logging.DEBUG


def test_create_app_loads_docker_config(monkeypatch, isolated_app_factory):
    docker_config = ModuleType('powerdnsadmin.docker_config')
    docker_config.DOCKER_CONFIG_LOADED = True
    docker_config.HSTS_ENABLED = False
    docker_config.SESSION_TYPE = None
    monkeypatch.setitem(
        sys.modules, 'powerdnsadmin.docker_config', docker_config)

    docker_config_path = os.path.join(powerdnsadmin.__path__[0],
                                      'docker_config.py')
    original_exists = os.path.exists
    monkeypatch.setattr(
        os.path, 'exists',
        lambda path: (path == docker_config_path or original_exists(path)))

    app = powerdnsadmin.create_app()

    assert app.config['DOCKER_CONFIG_LOADED'] is True


def test_create_app_ignores_non_python_string_config(isolated_app_factory):
    app = powerdnsadmin.create_app('production')

    assert 'production' not in app.config
