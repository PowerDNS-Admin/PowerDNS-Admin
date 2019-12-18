import json
import pytest
from unittest.mock import patch
from collections import namedtuple
import sys
import os
sys.path.append(os.getcwd())

import powerdnsadmin
from powerdnsadmin.models.setting import Setting
from powerdnsadmin.models.domain import Domain
from powerdnsadmin.models.api_key import ApiKey
from powerdnsadmin.models.role import Role
from powerdnsadmin.lib.validators import validate_zone
from powerdnsadmin.lib.schema import DomainSchema, ApiKeySchema
from tests.fixtures import client, initial_data, created_zone_data
from tests.fixtures import user_apikey, admin_apikey, zone_data
from tests.fixtures import admin_apikey_data, load_data


class TestUnitApiZoneAdminApiKey(object):
    @pytest.fixture
    def common_data_mock(self):
        self.google_setting_patcher = patch(
            'powerdnsadmin.services.google.Setting',
            spec=powerdnsadmin.models.setting.Setting)
        self.github_setting_patcher = patch(
            'powerdnsadmin.services.github.Setting',
            spec=powerdnsadmin.models.setting.Setting)
        self.oidc_setting_patcher = patch(
            'powerdnsadmin.services.oidc.Setting',
            spec=powerdnsadmin.models.setting.Setting)
        self.helpers_setting_patcher = patch(
            'powerdnsadmin.lib.helper.Setting',
            spec=powerdnsadmin.models.setting.Setting)
        self.models_setting_patcher = patch(
            'powerdnsadmin.models.setting.Setting',
            spec=powerdnsadmin.models.setting.Setting)
        self.domain_model_setting_patcher = patch(
            'powerdnsadmin.models.domain.Setting',
            spec=powerdnsadmin.models.setting.Setting)
        self.record_model_setting_patcher = patch(
            'powerdnsadmin.models.record.Setting',
            spec=powerdnsadmin.models.setting.Setting)
        self.server_model_setting_patcher = patch(
            'powerdnsadmin.models.server.Setting',
            spec=powerdnsadmin.models.setting.Setting)
        self.mock_apikey_patcher = patch(
            'powerdnsadmin.decorators.ApiKey',
            spec=powerdnsadmin.models.api_key.ApiKey)
        self.mock_hist_patcher = patch(
            'powerdnsadmin.routes.api.History',
            spec=powerdnsadmin.models.history.History)
        self.mock_setting_patcher = patch(
            'powerdnsadmin.routes.api.Setting',
            spec=powerdnsadmin.models.setting.Setting)

        data = admin_apikey_data()
        api_key = ApiKey(desc=data['description'],
                         role_name=data['role'],
                         domains=[])
        api_key.role = Role(name=data['role'])

        self.mock_google_setting = self.google_setting_patcher.start()
        self.mock_github_setting = self.github_setting_patcher.start()
        self.mock_oidc_setting = self.oidc_setting_patcher.start()
        self.mock_helpers_setting = self.helpers_setting_patcher.start()
        self.mock_models_setting = self.models_setting_patcher.start()
        self.mock_domain_model_setting = self.domain_model_setting_patcher.start(
        )
        self.mock_record_model_setting = self.record_model_setting_patcher.start(
        )
        self.mock_server_model_setting = self.server_model_setting_patcher.start(
        )
        self.mock_apikey = self.mock_apikey_patcher.start()
        self.mock_hist = self.mock_hist_patcher.start()
        self.mock_setting = self.mock_setting_patcher.start()

        self.mock_google_setting.return_value.get.side_effect = load_data
        self.mock_github_setting.return_value.get.side_effect = load_data
        self.mock_oidc_setting.return_value.get.side_effect = load_data
        self.mock_helpers_setting.return_value.get.side_effect = load_data
        self.mock_models_setting.return_value.get.side_effect = load_data
        self.mock_domain_model_setting.return_value.get.side_effect = load_data
        self.mock_record_model_setting.return_value.get.side_effect = load_data
        self.mock_server_model_setting.return_value.get.side_effect = load_data
        self.mock_apikey.return_value.is_validate.return_value = api_key

    def test_empty_get(self, client, common_data_mock, admin_apikey):
        with patch('powerdnsadmin.routes.api.Domain') as mock_domain, \
             patch('powerdnsadmin.lib.utils.requests.get') as mock_get:
            mock_domain.return_value.domains.return_value = []
            mock_domain.query.all.return_value = []
            mock_get.return_value.json.return_value = []
            mock_get.return_value.status_code = 200

            res = client.get("/api/v1/servers/pdnsadmin/zones",
                             headers=admin_apikey)

            data = res.get_json(force=True)
            assert res.status_code == 200
            assert data == []

    def test_create_zone(self, client, common_data_mock, zone_data,
                         admin_apikey, created_zone_data):
        with patch('powerdnsadmin.lib.helper.requests.request') as mock_post, \
             patch('powerdnsadmin.routes.api.Domain') as mock_domain:
            mock_post.return_value.status_code = 201
            mock_post.return_value.content = json.dumps(created_zone_data)
            mock_post.return_value.headers = {}
            mock_domain.return_value.update.return_value = True

            res = client.post("/api/v1/servers/localhost/zones",
                              headers=admin_apikey,
                              data=json.dumps(zone_data),
                              content_type="application/json")
            data = res.get_json(force=True)
            data['rrsets'] = []

            validate_zone(data)
            assert res.status_code == 201

    def test_get_multiple_zones(self, client, common_data_mock, zone_data,
                                admin_apikey):
        with patch('powerdnsadmin.routes.api.Domain') as mock_domain:
            test_domain = Domain(1, name=zone_data['name'].rstrip("."))
            mock_domain.query.all.return_value = [test_domain]

            res = client.get("/api/v1/servers/pdnsadmin/zones",
                             headers=admin_apikey)
            data = res.get_json(force=True)

            fake_domain = namedtuple("Domain",
                                     data[0].keys())(*data[0].values())
            domain_schema = DomainSchema(many=True)

            json.dumps(domain_schema.dump([fake_domain]))
            assert res.status_code == 200

    def test_delete_zone(self, client, common_data_mock, zone_data,
                         admin_apikey):
        with patch('powerdnsadmin.lib.utils.requests.request') as mock_delete, \
             patch('powerdnsadmin.routes.api.Domain') as mock_domain:
            mock_domain.return_value.update.return_value = True
            mock_delete.return_value.status_code = 204
            mock_delete.return_value.content = ''

            zone_url_format = "/api/v1/servers/localhost/zones/{0}"
            zone_url = zone_url_format.format(zone_data['name'].rstrip("."))
            res = client.delete(zone_url, headers=admin_apikey)

            assert res.status_code == 204
