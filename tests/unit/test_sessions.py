def test_public_routes_use_the_configured_session_backend(initial_data, client):
    login_response = client.get('/login')
    healthcheck_response = client.get('/healthcheck')

    assert login_response.status_code == 200
    assert healthcheck_response.status_code == 200
    assert healthcheck_response.get_data(as_text=True) == 'ok'
