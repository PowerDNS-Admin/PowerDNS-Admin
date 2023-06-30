import pytest
import json
from collections import namedtuple

from powerdnsadmin.lib.validators import validate_apikey
from powerdnsadmin.lib.schema import ApiKeySchema
from tests.conftest import user_apikey_data, admin_apikey_data


class TestIntegrationApiApiKeyAdminUser(object):
    def test_empty_get(self, initial_data, client, basic_auth_admin_headers):
        res = client.get("/api/v1/pdnsadmin/apikeys",
                         headers=basic_auth_admin_headers)
        data = res.get_json(force=True)
        assert res.status_code == 200
        assert data == []

    @pytest.mark.parametrize(
        "apikey_data",
        [user_apikey_data(), admin_apikey_data()])
    def test_create_apikey(self, initial_data, client, apikey_data, zone_data,
                           basic_auth_admin_headers):
        res = client.post("/api/v1/pdnsadmin/zones",
                          headers=basic_auth_admin_headers,
                          data=json.dumps(zone_data),
                          content_type="application/json")
        data = res.get_json(force=True)

        assert res.status_code == 201

        res = client.post("/api/v1/pdnsadmin/apikeys",
                          headers=basic_auth_admin_headers,
                          data=json.dumps(apikey_data),
                          content_type="application/json")
        data = res.get_json(force=True)

        validate_apikey(data)
        assert res.status_code == 201

        apikey_url_format = "/api/v1/pdnsadmin/apikeys/{0}"
        apikey_url = apikey_url_format.format(data['id'])

        res = client.delete(apikey_url, headers=basic_auth_admin_headers)

        assert res.status_code == 204

        zone_url_format = "/api/v1/pdnsadmin/zones/{0}"
        zone_url = zone_url_format.format(zone_data['name'].rstrip("."))
        res = client.delete(zone_url, headers=basic_auth_admin_headers)

        assert res.status_code == 204

    @pytest.mark.parametrize(
        "apikey_data",
        [user_apikey_data(), admin_apikey_data()])
    def test_get_multiple_apikey(self, initial_data, client, apikey_data,
                                 zone_data, basic_auth_admin_headers):
        res = client.post("/api/v1/pdnsadmin/zones",
                          headers=basic_auth_admin_headers,
                          data=json.dumps(zone_data),
                          content_type="application/json")
        data = res.get_json(force=True)

        assert res.status_code == 201

        res = client.post("/api/v1/pdnsadmin/apikeys",
                          headers=basic_auth_admin_headers,
                          data=json.dumps(apikey_data),
                          content_type="application/json")
        data = res.get_json(force=True)

        validate_apikey(data)
        assert res.status_code == 201

        res = client.get("/api/v1/pdnsadmin/apikeys",
                         headers=basic_auth_admin_headers)
        data = res.get_json(force=True)

        fake_role = namedtuple(
            "Role", data[0]['role'].keys())(*data[0]['role'].values())

        data[0]['domains'] = []
        data[0]['role'] = fake_role
        fake_apikey = namedtuple("ApiKey", data[0].keys())(*data[0].values())
        apikey_schema = ApiKeySchema(many=True)

        json.dumps(apikey_schema.dump([fake_apikey]))
        assert res.status_code == 200

        apikey_url_format = "/api/v1/pdnsadmin/apikeys/{0}"
        apikey_url = apikey_url_format.format(fake_apikey.id)
        res = client.delete(apikey_url, headers=basic_auth_admin_headers)

        assert res.status_code == 204

        zone_url_format = "/api/v1/pdnsadmin/zones/{0}"
        zone_url = zone_url_format.format(zone_data['name'].rstrip("."))
        res = client.delete(zone_url, headers=basic_auth_admin_headers)

        assert res.status_code == 204

    @pytest.mark.parametrize(
        "apikey_data",
        [user_apikey_data(), admin_apikey_data()])
    def test_delete_apikey(self, initial_data, client, apikey_data, zone_data,
                           basic_auth_admin_headers):
        res = client.post("/api/v1/pdnsadmin/zones",
                          headers=basic_auth_admin_headers,
                          data=json.dumps(zone_data),
                          content_type="application/json")
        data = res.get_json(force=True)

        assert res.status_code == 201

        res = client.post("/api/v1/pdnsadmin/apikeys",
                          headers=basic_auth_admin_headers,
                          data=json.dumps(apikey_data),
                          content_type="application/json")
        data = res.get_json(force=True)

        validate_apikey(data)
        assert res.status_code == 201

        apikey_url_format = "/api/v1/pdnsadmin/apikeys/{0}"
        apikey_url = apikey_url_format.format(data['id'])
        res = client.delete(apikey_url, headers=basic_auth_admin_headers)

        assert res.status_code == 204

        zone_url_format = "/api/v1/pdnsadmin/zones/{0}"
        zone_url = zone_url_format.format(zone_data['name'].rstrip("."))
        res = client.delete(zone_url, headers=basic_auth_admin_headers)

        assert res.status_code == 204
