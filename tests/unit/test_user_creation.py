from powerdnsadmin.models.base import db
from powerdnsadmin.models.user import User


def test_local_user_creation_rejects_case_insensitive_duplicate(initial_data,
                                                                 app):
    with app.app_context():
        existing = User.query.filter_by(username=app.config['TEST_USER']).one()
        original_count = User.query.count()

        duplicate = User(
            username=existing.username.upper(),
            plain_text_password='not-used',
            email='different@example.com',
        )
        result = duplicate.create_local_user()

        assert result == {
            'status': False,
            'msg': 'Username is already in use',
        }
        assert User.query.count() == original_count
        assert db.session.get(User, existing.id).username == existing.username
