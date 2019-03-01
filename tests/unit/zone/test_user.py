import os
import pytest
from unittest.mock import patch, MagicMock
import sys
import json
from collections import namedtuple
import logging as logger
sys.path.append(os.getcwd())
import app
from app.validators import validate_zone
from app.models import User, Domain, Role
from app.schema import DomainSchema
from tests.fixtures import client, basic_auth_user_headers
from tests.fixtures import zone_data, created_zone_data, load_data


class TestUnitApiZoneUser(object):

    @pytest.fixture
    def common_data_mock(self):
        self.oauth_setting_patcher = patch(
            'app.oauth.Setting',
            spec=app.models.Setting
        )
        self.api_setting_patcher = patch(
            'app.blueprints.api.Setting',
            spec=app.models.Setting
        )
        self.views_setting_patcher = patch(
            'app.views.Setting',
            spec=app.models.Setting
        )
        self.helpers_setting_patcher = patch(
            'app.lib.helper.Setting',
            spec=app.models.Setting
        )
        self.models_setting_patcher = patch(
            'app.models.Setting',
            spec=app.models.Setting
        )
        self.decorators_setting_patcher = patch(
            'app.decorators.Setting'
        )
        self.mock_user_patcher = patch(
            'app.decorators.User'
        )
        self.mock_hist_patcher = patch(
            'app.blueprints.api.History',
            spec=app.models.History
        )

        self.mock_oauth_setting = self.oauth_setting_patcher.start()
        self.mock_views_setting = self.views_setting_patcher.start()
        self.mock_helpers_setting = self.helpers_setting_patcher.start()
        self.mock_models_setting = self.models_setting_patcher.start()
        self.decorators_setting = self.decorators_setting_patcher.start()
        self.api_setting = self.api_setting_patcher.start()
        self.mock_user = self.mock_user_patcher.start()
        self.mock_hist = self.mock_hist_patcher.start()

        self.mock_oauth_setting.return_value.get.side_effect = load_data
        self.mock_views_setting.return_value.get.side_effect = load_data
        self.mock_helpers_setting.return_value.get.side_effect = load_data
        self.mock_models_setting.return_value.get.side_effect = load_data
        self.decorators_setting.return_value.get.side_effect = load_data
        self.api_setting.return_value.get.side_effect = load_data
        self.mockk = MagicMock()
        self.mockk.role.name = "User"
        self.mock_user.query.filter.return_value.first.return_value = self.mockk
        self.mock_user.return_value.is_validate.return_value = True

    def test_create_zone(
        self,
        client,
        common_data_mock,
        zone_data,
        basic_auth_user_headers,
        created_zone_data
    ):
        with patch('app.lib.helper.requests.request') as mock_post, \
             patch('app.blueprints.api.Domain') as mock_domain:
            mock_post.return_value.status_code = 201
            mock_post.return_value.content = json.dumps(created_zone_data)
            mock_post.return_value.headers = {}
            mock_domain.return_value.update.return_value = True

            res = client.post(
                "/api/v1/pdnsadmin/zones",
                headers=basic_auth_user_headers,
                data=json.dumps(zone_data),
                content_type="application/json"
            )
            data = res.get_json(force=True)
            data['rrsets'] = []

            validate_zone(data)
            assert res.status_code == 201

    def test_get_multiple_zones(
        self,
        client,
        common_data_mock,
        zone_data,
        basic_auth_user_headers
    ):
        test_domain = Domain(1, name=zone_data['name'].rstrip("."))
        self.mockk.get_domains.return_value = [test_domain]

        res = client.get(
            "/api/v1/pdnsadmin/zones",
            headers=basic_auth_user_headers
        )
        data = res.get_json(force=True)

        fake_domain = namedtuple(
            "Domain",
            data[0].keys()
        )(*data[0].values())
        domain_schema = DomainSchema(many=True)

        json.dumps(domain_schema.dump([fake_domain]))
        assert res.status_code == 200

    def test_delete_zone(
        self,
        client,
        common_data_mock,
        zone_data,
        basic_auth_user_headers
    ):
        with patch('app.lib.utils.requests.request') as mock_delete, \
             patch('app.blueprints.api.Domain') as mock_domain:
            mock_domain.return_value.update.return_value = True
            test_domain = Domain(1, name=zone_data['name'].rstrip("."))
            self.mockk.get_domains.return_value = [test_domain]
            mock_delete.return_value.status_code = 204
            mock_delete.return_value.content = ''

            zone_url_format = "/api/v1/pdnsadmin/zones/{0}"
            zone_url = zone_url_format.format(zone_data['name'].rstrip("."))
            res = client.delete(
                zone_url,
                headers=basic_auth_user_headers
            )

            assert res.status_code == 204
