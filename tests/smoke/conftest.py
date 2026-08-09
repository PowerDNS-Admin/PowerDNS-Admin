import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def release_version():
    version = (REPO_ROOT / 'powerdnsadmin' / 'VERSION').read_text(
        encoding='utf-8').strip()
    assert version, 'VERSION file must contain a release version'
    return version


def csrf_token(response):
    match = re.search(
        rb'name="_csrf_token" value="([^"]+)"',
        response.data,
    )
    assert match is not None, 'login form is missing a CSRF token'
    return match.group(1).decode('utf-8')


@pytest.fixture
def logged_in_admin_client(app, client, initial_data):
    login_page = client.get('/login')
    assert login_page.status_code == 200

    login_response = client.post(
        '/login',
        data={
            'username': app.config['TEST_ADMIN_USER'],
            'password': app.config['TEST_ADMIN_PASSWORD'],
            'auth_method': 'LOCAL',
            '_csrf_token': csrf_token(login_page),
        },
    )
    assert login_response.status_code == 302

    return client
