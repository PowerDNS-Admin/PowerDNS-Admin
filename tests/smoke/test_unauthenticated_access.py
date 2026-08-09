import pytest


PROTECTED_PAGES = (
    '/dashboard/v2/',
    '/dashboard/v2/domains/forward',
    '/domain/add',
    '/user/profile',
    '/admin/history',
    '/admin/manage-user',
    '/admin/manage-account',
    '/admin/manage-keys',
    '/admin/templates',
    '/admin/template/create',
    '/admin/global-search',
    '/admin/server/statistics',
    '/admin/server/configuration',
    '/admin/setting/basic',
    '/admin/setting/authentication',
)


@pytest.mark.parametrize('path', PROTECTED_PAGES)
def test_protected_pages_redirect_anonymous_users_to_login(
        initial_data, client, path):
    response = client.get(path)

    assert response.status_code == 302, (
        f'{path} returned {response.status_code} instead of redirecting')
    assert response.headers['Location'].endswith('/login')
