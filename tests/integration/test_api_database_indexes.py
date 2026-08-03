from sqlalchemy import inspect

from powerdnsadmin.models.base import db


EXPECTED_API_INDEXES = {
    'account_user': {
        'ix_account_user_user_id_account_id': ['user_id', 'account_id'],
    },
    'apikey_account': {
        'ix_apikey_account_apikey_id_account_id': [
            'apikey_id', 'account_id'],
    },
    'domain_apikey': {
        'ix_domain_apikey_apikey_id_domain_id': ['apikey_id', 'domain_id'],
    },
    'domain_setting': {
        'ix_domain_setting_domain_id_setting': ['domain_id', 'setting'],
    },
    'domain_user': {
        'ix_domain_user_user_id_domain_id': ['user_id', 'domain_id'],
    },
}


def test_api_access_path_indexes_exist(app, initial_data):
    with app.app_context():
        inspector = inspect(db.engine)
        actual_indexes = {
            table_name: {
                index['name']: index['column_names']
                for index in inspector.get_indexes(table_name)
            }
            for table_name in EXPECTED_API_INDEXES
        }

    for table_name, expected_indexes in EXPECTED_API_INDEXES.items():
        for index_name, columns in expected_indexes.items():
            assert actual_indexes[table_name][index_name] == columns
