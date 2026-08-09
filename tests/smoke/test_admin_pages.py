import pytest


ADMIN_PAGES = (
    '/admin/history',
    '/admin/manage-user',
    '/admin/manage-account',
    '/admin/manage-keys',
    '/admin/user/edit',
    '/admin/account/edit',
    '/admin/key/edit',
    '/admin/setting/basic',
    '/admin/setting/authentication',
    '/admin/setting/pdns',
    '/admin/setting/dns-records',
    '/admin/templates',
    '/admin/templates/list',
    '/admin/template/create',
    '/admin/global-search',
    '/admin/server/statistics',
    '/admin/server/configuration',
)


@pytest.mark.parametrize('path', ADMIN_PAGES)
def test_admin_pages_render_for_administrator(logged_in_admin_client, path):
    response = logged_in_admin_client.get(path)
    body = response.get_data(as_text=True)

    assert response.status_code == 200, (
        f'{path} returned {response.status_code}: {body[:500]}')
    assert 'Traceback' not in body
    assert 'TemplateNotFound' not in body
    assert 'login-card-body' not in body
