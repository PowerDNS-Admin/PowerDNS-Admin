from flask_session.sqlalchemy import SqlAlchemySessionInterface


def test_app_uses_sqlalchemy_session_backend_from_test_config(app):
    assert app.config['SESSION_TYPE'] == 'sqlalchemy'
    assert isinstance(app.session_interface, SqlAlchemySessionInterface)


def test_login_page_persists_csrf_token_in_configured_session(
        initial_data, client):
    login_response = client.get('/login')

    assert login_response.status_code == 200
    assert client.get_cookie('session') is not None

    with client.session_transaction() as session:
        assert session.get('_csrf_token')
