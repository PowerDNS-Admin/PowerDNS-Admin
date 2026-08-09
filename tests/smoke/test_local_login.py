from .conftest import csrf_token


def test_local_login_establishes_authenticated_session(
        app, client, initial_data):
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

    dashboard_response = client.get('/dashboard/v2/')
    body = dashboard_response.get_data(as_text=True)

    assert dashboard_response.status_code == 200
    assert 'login-card-body' not in body
    assert 'id="dashboard-v2"' in body


def test_local_login_rejects_invalid_password(app, client, initial_data):
    login_page = client.get('/login')
    assert login_page.status_code == 200

    login_response = client.post(
        '/login',
        data={
            'username': app.config['TEST_ADMIN_USER'],
            'password': 'definitely-not-the-password',
            'auth_method': 'LOCAL',
            '_csrf_token': csrf_token(login_page),
        },
    )
    body = login_response.get_data(as_text=True)

    assert login_response.status_code == 200
    assert 'Invalid credentials' in body
    assert 'login-card-body' in body


def test_logout_clears_authenticated_session(logged_in_admin_client):
    logout_response = logged_in_admin_client.get('/logout')

    assert logout_response.status_code == 302
    assert logout_response.headers['Location'].endswith('/login')

    dashboard_response = logged_in_admin_client.get('/dashboard/v2/')

    assert dashboard_response.status_code == 302
    assert dashboard_response.headers['Location'].endswith('/login')
