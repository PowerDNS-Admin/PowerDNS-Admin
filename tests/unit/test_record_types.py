from flask import Flask

from powerdnsadmin.lib.settings import AppSettings
from powerdnsadmin.models.setting import Setting


NEW_RECORD_TYPES = {'APL', 'HTTPS', 'SVCB'}


def test_new_record_types_are_available_as_opt_in_settings():
    for setting_name in (
            'forward_records_allow_edit',
            'reverse_records_allow_edit'):
        record_types = AppSettings.defaults[setting_name]

        assert NEW_RECORD_TYPES <= record_types.keys()
        assert all(record_types[record_type] is False
                   for record_type in NEW_RECORD_TYPES)


def test_saved_record_settings_gain_new_types_without_losing_choices():
    app = Flask(__name__)
    app.config['FORWARD_RECORDS_ALLOW_EDIT'] = {
        'A': False,
        'CAA': True,
    }

    with app.app_context():
        record_types = Setting().get('forward_records_allow_edit')

    assert record_types['A'] is False
    assert record_types['CAA'] is True
    assert all(record_types[record_type] is False
               for record_type in NEW_RECORD_TYPES)
