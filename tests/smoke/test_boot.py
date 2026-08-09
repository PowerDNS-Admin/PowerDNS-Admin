import json

from .conftest import REPO_ROOT


def test_healthcheck_returns_ok(initial_data, client):
    response = client.get('/healthcheck')

    assert response.status_code == 200
    assert response.get_data(as_text=True) == 'ok'


def test_ping_returns_ok(initial_data, client):
    response = client.get('/ping')

    assert response.status_code == 200
    assert response.get_data(as_text=True) == 'ok'


def test_api_list_returns_v1_entrypoint(initial_data, client):
    response = client.get('/api')
    payload = json.loads(response.get_data(as_text=True))

    assert response.status_code == 200
    assert payload == [{'url': '/api/v1', 'version': 1}]


def test_swagger_spec_is_packaged_and_served(initial_data, client):
    response = client.get('/swagger')
    payload = response.get_json()

    assert response.status_code == 200
    assert response.headers['Content-Type'].startswith('application/json')
    assert payload['swagger'] == '2.0'
    assert payload['basePath'] == '/api/v1'
    assert 'paths' in payload


def test_login_page_renders_local_auth_form(initial_data, client):
    response = client.get('/login')
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'name="username"' in body
    assert 'name="password"' in body
    assert 'name="_csrf_token"' in body
    assert 'login-card-body' in body


def test_footer_template_uses_app_version_variable():
    template = (REPO_ROOT / 'powerdnsadmin' / 'templates' / 'base.html').read_text(
        encoding='utf-8')

    assert 'Version {{ APP_VERSION }}' in template
    assert 'Version 0.' not in template


def test_app_loads_version_from_version_file(app, release_version):
    assert app.config['APP_VERSION'] == release_version


def test_authenticated_footer_renders_release_version(
        logged_in_admin_client, release_version):
    response = logged_in_admin_client.get('/dashboard/v2/')
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert f'Version {release_version}' in body
    assert 'login-card-body' not in body
