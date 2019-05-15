import os
import pytest
import sys
import json
from base64 import b64encode
from collections import namedtuple
import logging as logger
sys.path.append(os.getcwd())
import app
from app.validators import validate_zone
from app.models import Setting
from app.schema import DomainSchema
from tests.fixtures import client
from tests.fixtures import zone_data, initial_apikey_data
from tests.fixtures import admin_apikey_integration


class TestIntegrationApiZoneAdminApiKey(object):

    def test_empty_get(self, client, initial_apikey_data, admin_apikey_integration):
        res = client.get(
            "/api/v1/servers/localhost/zones",
            headers=admin_apikey_integration
        )
        data = res.get_json(force=True)
        assert res.status_code == 200
        assert data == []

    def test_create_zone(
        self,
        client,
        initial_apikey_data,
        zone_data,
        admin_apikey_integration
    ):
        res = client.post(
            "/api/v1/servers/localhost/zones",
            headers=admin_apikey_integration,
            data=json.dumps(zone_data),
            content_type="application/json"
        )
        data = res.get_json(force=True)
        data['rrsets'] = []

        validate_zone(data)
        assert res.status_code == 201

        zone_url_format = "/api/v1/servers/localhost/zones/{0}"
        zone_url = zone_url_format.format(zone_data['name'].rstrip("."))
        res = client.delete(
            zone_url,
            headers=admin_apikey_integration
        )

        assert res.status_code == 204

    def test_get_multiple_zones(
        self,
        client,
        initial_apikey_data,
        zone_data,
        admin_apikey_integration
    ):
        res = client.post(
            "/api/v1/servers/localhost/zones",
            headers=admin_apikey_integration,
            data=json.dumps(zone_data),
            content_type="application/json"
        )
        data = res.get_json(force=True)
        data['rrsets'] = []

        validate_zone(data)
        assert res.status_code == 201

        res = client.get(
            "/api/v1/servers/localhost/zones",
            headers=admin_apikey_integration
        )
        data = res.get_json(force=True)
        fake_domain = namedtuple("Domain", data[0].keys())(*data[0].values())
        domain_schema = DomainSchema(many=True)

        json.dumps(domain_schema.dump([fake_domain]))
        assert res.status_code == 200

        zone_url_format = "/api/v1/servers/localhost/zones/{0}"
        zone_url = zone_url_format.format(zone_data['name'].rstrip("."))
        res = client.delete(
            zone_url,
            headers=admin_apikey_integration
        )

        assert res.status_code == 204

    def test_delete_zone(
        self,
        client,
        initial_apikey_data,
        zone_data,
        admin_apikey_integration
    ):
        res = client.post(
            "/api/v1/servers/localhost/zones",
            headers=admin_apikey_integration,
            data=json.dumps(zone_data),
            content_type="application/json"
        )
        data = res.get_json(force=True)
        data['rrsets'] = []

        validate_zone(data)
        assert res.status_code == 201

        zone_url_format = "/api/v1/servers/localhost/zones/{0}"
        zone_url = zone_url_format.format(zone_data['name'].rstrip("."))
        res = client.delete(
            zone_url,
            headers=admin_apikey_integration
        )

        assert res.status_code == 204
