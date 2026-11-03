import traceback
import pytimeparse
from ast import literal_eval
from flask import current_app
from .base import db
from powerdnsadmin.lib.settings import AppSettings
from powerdnsadmin.lib.setting_audit import queue_setting_change


class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    value = db.Column(db.Text())

    ZONE_TYPE_FORWARD = 'forward'
    ZONE_TYPE_REVERSE = 'reverse'
    # These stay on the process configuration. An administrator saving any
    # other setting makes that saved value the one the application uses,
    # including when the environment supplied an older value at startup.
    CONFIG_LOCKED = frozenset({
        'bind_address',
        'csrf_cookie_secure',
        'log_level',
        'pdns_admin_log_level',
        'port',
        'salt',
        'secret_key',
        'session_cookie_secure',
        'session_type',
        'sqlalchemy_engine_options',
        'sqlalchemy_track_modifications',
    })

    def __init__(self, id=None, name=None, value=None):
        self.id = id
        self.name = name
        self.value = value

    # allow database autoincrement to do its own ID assignments
    def __init__(self, name=None, value=None):
        self.id = None
        self.name = name
        self.value = value

    def set_maintenance(self, mode):
        maintenance = Setting.query.filter(
            Setting.name == 'maintenance').first()

        if maintenance is None:
            value = AppSettings.defaults['maintenance']
            maintenance = Setting(name='maintenance', value=str(value))
            db.session.add(maintenance)

        mode = str(mode)

        try:
            if maintenance.value != mode:
                old_value = maintenance.value
                maintenance.value = mode
                queue_setting_change('maintenance', old_value, mode)
                db.session.commit()
                self._publish('maintenance', mode)
            return True
        except Exception as e:
            current_app.logger.error('Cannot set maintenance to {0}. DETAIL: {1}'.format(
                mode, e))
            current_app.logger.debug(traceback.format_exec())
            db.session.rollback()
            return False

    def toggle(self, setting):
        current_setting = Setting.query.filter(Setting.name == setting).first()

        if current_setting is None:
            value = AppSettings.defaults[setting]
            current_setting = Setting(name=setting, value=str(value))
            db.session.add(current_setting)

        try:
            old_value = current_setting.value
            if current_setting.value == "True":
                current_setting.value = "False"
            else:
                current_setting.value = "True"
            queue_setting_change(setting, old_value, current_setting.value)
            db.session.commit()
            self._publish(setting, current_setting.value)
            return True
        except Exception as e:
            current_app.logger.error('Cannot toggle setting {0}. DETAIL: {1}'.format(
                setting, e))
            current_app.logger.debug(traceback.format_exec())
            db.session.rollback()
            return False

    def set(self, setting, value):
        import json
        current_setting = Setting.query.filter(Setting.name == setting).first()

        if current_setting is None:
            current_setting = Setting(name=setting, value=None)
            db.session.add(current_setting)

        value = AppSettings.convert_type(setting, value)

        if isinstance(value, dict) or isinstance(value, list):
            value = json.dumps(value)

        try:
            old_value = current_setting.value
            current_setting.value = value
            queue_setting_change(setting, old_value, value)
            db.session.commit()
            self._publish(setting, value)
            return True
        except Exception as e:
            current_app.logger.error('Cannot edit setting {0}. DETAIL: {1}'.format(setting, e))
            current_app.logger.debug(traceback.format_exec())
            db.session.rollback()
            return False

    def _publish(self, setting, value):
        """Keep this process aligned with a value just saved to the database."""
        if setting in self.CONFIG_LOCKED:
            return
        current_app.config[str(setting).upper()] = value

    def _saved_row(self, setting):
        """Return the stored row, or None when this app has no database.

        A Flask app that only carries configuration, such as a unit test,
        has no SQLAlchemy registration. Saved values still win once the
        application database is attached.
        """
        if 'sqlalchemy' not in current_app.extensions:
            return None
        return self.query.filter(Setting.name == setting).first()

    def get(self, setting):
        if setting in AppSettings.defaults:
            result = None
            if setting not in self.CONFIG_LOCKED:
                result = self._saved_row(setting)

            if result is None and setting.upper() in current_app.config:
                result = current_app.config[setting.upper()]

            if result is not None:
                if hasattr(result, 'value'):
                    result = result.value

                result = AppSettings.convert_type(setting, result)
                if setting in ('forward_records_allow_edit',
                               'reverse_records_allow_edit'):
                    # Keep saved administrator choices while making record
                    # types introduced by newer releases available to opt in.
                    result = {
                        **AppSettings.defaults[setting],
                        **result,
                    }
                return result
            else:
                return AppSettings.defaults[setting]
        else:
            current_app.logger.error('Unknown setting queried: {0}'.format(setting))

    def get_group(self, group):
        if not isinstance(group, list):
            group = AppSettings.groups[group]

        result = {}

        for var_name, default_value in AppSettings.defaults.items():
            if var_name in group:
                result[var_name] = self.get(var_name)

        return result

    def get_records_allow_to_edit(self):
        return sorted(
            set(self.get_supported_record_types(self.ZONE_TYPE_FORWARD) +
                self.get_supported_record_types(self.ZONE_TYPE_REVERSE)))

    def get_supported_record_types(self, zone_type):
        setting_value = []

        if zone_type == self.ZONE_TYPE_FORWARD:
            setting_value = self.get('forward_records_allow_edit')
        elif zone_type == self.ZONE_TYPE_REVERSE:
            setting_value = self.get('reverse_records_allow_edit')

        records = literal_eval(setting_value) if isinstance(setting_value, str) else setting_value
        types = [r for r in records if records[r]]

        return types

    def get_ttl_options(self):
        return [(pytimeparse.parse(ttl), ttl)
                for ttl in self.get('ttl_options').split(',')]
