def test_domain_add_page_renders_for_administrator(logged_in_admin_client):
    response = logged_in_admin_client.get('/domain/add')
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Traceback' not in body
    assert 'TemplateNotFound' not in body
    assert 'login-card-body' not in body
    assert 'id="domain_name"' in body
    assert 'name="radio_type"' in body


def test_user_profile_page_renders_for_administrator(logged_in_admin_client):
    response = logged_in_admin_client.get('/user/profile')
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Traceback' not in body
    assert 'TemplateNotFound' not in body
    assert 'login-card-body' not in body
    assert 'Profile Editor' in body
    assert 'name="firstname"' in body
