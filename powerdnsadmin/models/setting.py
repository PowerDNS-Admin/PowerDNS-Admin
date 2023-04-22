import sys
import pytimeparse
from ast import literal_eval
from flask import current_app
from .base import db
from powerdnsadmin.lib.settings import Settings
from powerdnsadmin.lib.settings_config import SettingMap


class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    value = db.Column(db.Text())

    ZONE_TYPE_FORWARD = 'forward'
    ZONE_TYPE_REVERSE = 'reverse'

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
        setting = Settings.instance().get(SettingMap.MAINTENANCE)
        mode = str(mode)

        if setting.value != mode:
            setting.value = mode
            return setting.save()

        return True

    def toggle(self, name):
        setting = Settings.instance().get(name)

        if not setting.stype == bool:
            current_app.logger.error('Cannot toggle setting {0}. DETAIL: Setting is not of boolean type'.format(name))
            return False

        setting.value = not setting.value
        return setting.save()

    def set(self, name, value):
        settings = Settings.instance()

        if not settings.has(name):
            current_app.logger.error('Unknown setting specified: {0}'.format(name))
            return False

        setting = settings.get(name)
        setting.set(value)
        setting.loaded = True

        return setting.save()

    def get(self, name):
        """ Returns the value (or default) of the specified setting, otherwise None if the setting doesn't exist. """
        settings = Settings.instance()

        if not settings.has(name):
            current_app.logger.error('Unknown setting specified: {0}'.format(name))
            return None

        setting = settings.get(name)

        if not setting.loaded:
            return setting.default

        return setting.value

    def get_all(self):
        """ Returns all settings with their associated values as a simple dictionary. """
        result = {}
        for name, setting in Settings.instance().all().items():
            result[name] = setting.value if setting.loaded else setting.default
        return result

    def get_records_allow_to_edit(self):
        return list(
            set(self.get_supported_record_types(self.ZONE_TYPE_FORWARD) +
                self.get_supported_record_types(self.ZONE_TYPE_REVERSE)))

    def get_supported_record_types(self, zone_type):
        setting_value = []

        if zone_type == self.ZONE_TYPE_FORWARD:
            setting_value = self.get(SettingMap.FORWARD_RECORDS_ALLOW_EDIT)
        elif zone_type == self.ZONE_TYPE_REVERSE:
            setting_value = self.get(SettingMap.REVERSE_RECORDS_ALLOW_EDIT)

        records = literal_eval(setting_value) if isinstance(setting_value, str) else setting_value
        types = [r for r in records if records[r]]

        # Sort alphabetically if python version is smaller than 3.6
        if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 6):
            types.sort()

        return types

    def get_ttl_options(self):
        return [(pytimeparse.parse(ttl), ttl)
                for ttl in self.get(SettingMap.TTL_OPTIONS).split(',')]
