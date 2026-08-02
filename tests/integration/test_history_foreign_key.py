from sqlalchemy import inspect

from powerdnsadmin.models.base import db


def test_history_domain_foreign_key_sets_null_on_delete(app, initial_data):
    with app.app_context():
        foreign_keys = inspect(db.engine).get_foreign_keys('history')

    domain_foreign_key = next(
        foreign_key for foreign_key in foreign_keys
        if foreign_key['constrained_columns'] == ['domain_id']
    )

    assert domain_foreign_key['referred_table'] == 'domain'
    assert domain_foreign_key['options']['ondelete'].upper() == 'SET NULL'
