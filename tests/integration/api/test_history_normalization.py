import json

from powerdnsadmin.models.history import History
from powerdnsadmin.routes import api as api_routes


class SuccessfulResponse:
    status_code = 204
    content = b''
    headers = {}


def test_api_record_history_normalizes_null_comments(
        app, client, initial_apikey_data, admin_apikey_integration,
        monkeypatch):
    with app.app_context():
        app_settings = {
            'bg_domain_updates': True,
            'enable_api_rr_history': True,
        }
        monkeypatch.setattr(
            api_routes.Setting,
            'get',
            lambda self, key: app_settings.get(key),
        )
        monkeypatch.setattr(
            api_routes.Domain,
            'update',
            lambda self: None,
        )
        monkeypatch.setattr(
            api_routes.Domain,
            'get_id_by_name',
            lambda self, name: None,
        )
        monkeypatch.setattr(
            api_routes.helper,
            'forward_request',
            lambda: SuccessfulResponse(),
        )

        response = client.patch(
            '/api/v1/servers/localhost/zones/example.org.',
            headers=admin_apikey_integration,
            json={
                'rrsets': [{
                    'name': 'example.org.',
                    'type': 'TXT',
                    'changetype': 'REPLACE',
                    'ttl': 60,
                    'records': [{
                        'content': 'challenge',
                        'disabled': False,
                    }],
                    'comments': None,
                }],
            },
        )

        assert response.status_code == 204
        history = History.query.filter_by(
            msg='Apply record changes to zone example.org').order_by(
                History.id.desc()).first()
        assert history is not None
        assert json.loads(history.detail)['add_rrsets'][0]['comments'] == []
