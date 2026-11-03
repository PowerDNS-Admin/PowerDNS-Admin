import os
import re

import pytest

from flask import session
from flask_login import login_user

from powerdnsadmin.lib.setting_audit import (
    display_setting_value,
    setting_value_is_secret,
)
from powerdnsadmin.models.base import db
from powerdnsadmin.models.setting import Setting
from powerdnsadmin.models.system_history import SystemHistory
from powerdnsadmin.models.user import User


@pytest.fixture(autouse=True)
def in_app_connection_settings(app, monkeypatch):
    # Audit tests exercise installations that configure the connection in-app.
    monkeypatch.setitem(app.config, '_PDNS_CONNECTION_SETTINGS', {})


def test_credential_settings_are_redacted():
    assert setting_value_is_secret('pdns_api_key')
    assert setting_value_is_secret('ldap_admin_password')
    assert setting_value_is_secret('google_oauth_client_secret')
    assert setting_value_is_secret('oidc_oauth_key')
    assert not setting_value_is_secret('pdns_api_url')
    assert not setting_value_is_secret('google_token_url')
    assert not setting_value_is_secret('site_name')

    assert display_setting_value('pdns_api_key', 'live-key') == '[redacted]'
    assert display_setting_value('pdns_api_key', '') == ''
    assert display_setting_value('pdns_api_url', 'http://10.1.1.1:8081') == (
        'http://10.1.1.1:8081')


def test_setting_change_records_actor_and_hides_the_key(
        app, initial_data):
    with app.app_context():
        original_site = Setting().get('site_name')
        original_key = Setting().get('pdns_api_key')
        original_otp = Setting().get('otp_force')
    try:
        _assert_setting_audit(app)
    finally:
        # Saving a setting also copies it onto the process. The database is
        # rebuilt for the next module, so put the process copy back too.
        with app.app_context():
            Setting().set('site_name', original_site)
            Setting().set('pdns_api_key', original_key)
            Setting().set('otp_force', 'True' if original_otp else 'False')
            Setting().set_maintenance(False)


def _assert_setting_audit(app):
    with app.app_context():
        admin = User.query.filter_by(
            username=app.config['TEST_ADMIN_USER']).one()
        site_before = SystemHistory.query.filter_by(
            setting_name='site_name').count()

        with app.test_request_context('/admin/setting/pdns'):
            login_user(admin)
            session['session_version'] = admin.session_version or 0
            assert Setting().set('site_name', 'Audit Site')
            assert Setting().set('site_name', 'Audit Site')
            assert Setting().set('pdns_api_key', 'replacement-secret-key')
            assert Setting().toggle('otp_force')
            assert Setting().set_maintenance(True)

        site_rows = SystemHistory.query.filter_by(
            setting_name='site_name').order_by(SystemHistory.id.asc()).all()
        key_row = SystemHistory.query.filter_by(
            setting_name='pdns_api_key').order_by(
                SystemHistory.id.desc()).first()
        api_key = os.environ.get('PDNS_API_KEY') or ''

        assert len(site_rows) == site_before + 1
        assert site_rows[-1].username == admin.username
        assert site_rows[-1].user_id == admin.id
        assert site_rows[-1].new_value == 'Audit Site'
        assert key_row.new_value == '[redacted]'
        assert 'replacement-secret-key' not in (key_row.new_value or '')
        assert 'replacement-secret-key' not in (key_row.old_value or '')
        if api_key:
            assert api_key not in (key_row.old_value or '')
            assert api_key not in (key_row.new_value or '')

        toggled = SystemHistory.query.filter_by(
            setting_name='otp_force').order_by(SystemHistory.id.desc()).first()
        maintained = SystemHistory.query.filter_by(
            setting_name='maintenance').order_by(
                SystemHistory.id.desc()).first()
        assert toggled.username == admin.username
        assert toggled.old_value != toggled.new_value
        assert maintained.username == admin.username
        assert maintained.new_value == 'True'


def test_system_activity_page_is_limited_to_operators(
        app, client, initial_data):
    with app.app_context():
        admin = User.query.filter_by(
            username=app.config['TEST_ADMIN_USER']).one()
        user = User.query.filter_by(
            username=app.config['TEST_USER']).one()
        admin_id = admin.id
        admin_version = admin.session_version or 0
        user_id = user.id
        user_version = user.session_version or 0
        Setting().set('pdns_api_url', 'http://192.0.2.10:8081')

    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True
        session['session_version'] = user_version
        session['authentication_type'] = 'LOCAL'
    denied = client.get('/admin/system-activity')
    assert denied.status_code == 403

    with client.session_transaction() as session:
        session['_user_id'] = str(admin_id)
        session['_fresh'] = True
        session['session_version'] = admin_version
        session['authentication_type'] = 'LOCAL'
    page = client.get('/admin/system-activity')
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert 'pdns_api_url' in body
    assert 'http://192.0.2.10:8081' in body

    filtered = client.get('/admin/system-activity?setting=pdns_api_url')
    assert filtered.status_code == 200
    assert 'pdns_api_url' in filtered.get_data(as_text=True)


def test_saved_pdns_url_replaces_the_process_copy(app, initial_data):
    with app.app_context():
        app.config['PDNS_API_URL'] = 'http://from-env.example:8081'
        stored_before = Setting.query.filter_by(name='pdns_api_url').one().value
        assert stored_before != 'http://from-env.example:8081'
        assert Setting().get('pdns_api_url') == stored_before

        assert Setting().set('pdns_api_url', 'http://saved.example:8082')
        assert Setting().get('pdns_api_url') == 'http://saved.example:8082'
        assert app.config['PDNS_API_URL'] == 'http://saved.example:8082'

        Setting.query.filter_by(name='pdns_api_url').delete()
        db.session.commit()
        app.config['PDNS_API_URL'] = 'http://from-env.example:8081'
        assert Setting().get('pdns_api_url') == 'http://from-env.example:8081'

        app.config['SECRET_KEY'] = 'process-secret-value'
        assert Setting().set('secret_key', 'database-secret-value')
        assert Setting().get('secret_key') == 'process-secret-value'
        assert app.config['SECRET_KEY'] == 'process-secret-value'


def test_pdns_settings_page_keeps_the_saved_url(app, client, initial_data):
    with app.app_context():
        admin = User.query.filter_by(
            username=app.config['TEST_ADMIN_USER']).one()
        admin_id = admin.id
        admin_version = admin.session_version or 0
        current_key = Setting().get('pdns_api_key')
        app.config['PDNS_API_URL'] = 'http://from-env.example:8081'
        app.config['PDNS_API_KEY'] = 'environment-key'

    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_id)
        sess['_fresh'] = True
        sess['session_version'] = admin_version
        sess['authentication_type'] = 'LOCAL'

    page = client.get('/admin/setting/pdns')
    assert page.status_code == 200
    token = re.search(
        rb'name="_csrf_token" value="([^"]+)"', page.data).group(1).decode()
    saved = client.post(
        '/admin/setting/pdns',
        data={
            '_csrf_token': token,
            'pdns_api_url': 'http://saved.example:8082',
            'pdns_api_key': current_key,
        },
    )
    assert saved.status_code == 200
    assert 'value="http://saved.example:8082"' in saved.get_data(as_text=True)

    again = client.get('/admin/setting/pdns')
    assert 'value="http://saved.example:8082"' in again.get_data(as_text=True)
    with app.app_context():
        assert Setting().get('pdns_api_url') == 'http://saved.example:8082'


@pytest.mark.parametrize('locked_names', [
    ('pdns_api_url',), ('pdns_api_key',), ('pdns_api_url', 'pdns_api_key'),
])
def test_deployment_connection_is_read_only(
        app, client, initial_data, monkeypatch, locked_names):
    values = {'pdns_api_url': 'http://deployment.example:8081',
              'pdns_api_key': 'deployment-key'}
    monkeypatch.setitem(app.config, '_PDNS_CONNECTION_SETTINGS', {
        name: {'value': values[name], 'source': 'environment'}
        for name in locked_names
    })
    with app.app_context():
        admin = User.query.filter_by(username=app.config['TEST_ADMIN_USER']).one()
        admin_id, version = admin.id, admin.session_version or 0
        before = {name: Setting.query.filter_by(name=name).one().value
                  for name in values}
        history_count = SystemHistory.query.count()
        for name in locked_names:
            monkeypatch.setitem(app.config, name.upper(), 'stale-process-value')
            assert Setting().get(name) == values[name]
            assert not Setting().set(name, 'forged')
            assert not Setting().toggle(name)

    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_id)
        sess['_fresh'] = True
        sess['session_version'] = version
        sess['authentication_type'] = 'LOCAL'

    page = client.get('/admin/setting/pdns')
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert 'Managed by environment' in body
    for name in locked_names:
        assert re.search(r'name="' + name + r'"[^>]*readonly', body)
    token = re.search(rb'name="_csrf_token" value="([^"]+)"', page.data).group(1).decode()
    forged = client.post('/admin/setting/pdns', data={
        '_csrf_token': token, 'pdns_api_url': 'http://forged.example',
        'pdns_api_key': 'forged-key',
    })
    assert forged.status_code == 400
    with app.app_context():
        assert SystemHistory.query.count() == history_count
        for name in values:
            assert Setting.query.filter_by(name=name).one().value == before[name]

    # Read-only inputs may be omitted; editable connection fields still save.
    submitted = {name: values[name] for name in values if name not in locked_names}
    submitted['_csrf_token'] = token
    saved = client.post('/admin/setting/pdns', data=submitted)
    assert saved.status_code == 200
    with app.app_context():
        for name in values:
            assert Setting().get(name) == values[name]
            if name in locked_names:
                assert Setting.query.filter_by(name=name).one().value == before[name]
        # Removing deployment ownership exposes the original saved settings.
        monkeypatch.setitem(app.config, '_PDNS_CONNECTION_SETTINGS', {})
        for name in locked_names:
            assert Setting().get(name) == before[name]
