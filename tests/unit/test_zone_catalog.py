import re
from pathlib import Path
from unittest.mock import patch

from powerdnsadmin.models.domain import Domain
from powerdnsadmin.models.user import User


def test_zone_creation_without_catalog_is_backward_compatible(initial_data,
                                                               app, client):
    with app.app_context():
        admin_id = User.query.filter_by(
            username=app.config['TEST_ADMIN_USER']).one().id

    with client.session_transaction() as session:
        session['_user_id'] = str(admin_id)
        session['_fresh'] = True

    form_response = client.get('/domain/add')
    csrf_token = re.search(
        rb'name="_csrf_token" value="([^"]+)"',
        form_response.data,
    ).group(1).decode()

    form_data = {
        '_csrf_token': csrf_token,
        'domain_name': 'catalog-compatibility.example',
        'radio_type': 'native',
        'domain_template': '0',
        'radio_type_soa_edit_api': 'DEFAULT',
        'accountid': '0',
    }

    with patch.object(
            Domain, 'add',
            return_value={'status': 'error', 'msg': 'expected test response'}
    ) as add_zone:
        response = client.post('/domain/add', data=form_data)

    assert response.status_code == 400
    assert add_zone.call_args.kwargs['catalog_name'] is None


def test_powerdns_payload_omits_unselected_catalog(app):
    with app.app_context(), \
            patch('powerdnsadmin.models.domain.Setting') as setting, \
            patch('powerdnsadmin.models.domain.utils.fetch_json',
                  return_value={}) as fetch_json, \
            patch.object(Domain, 'add_domain_to_powerdns_admin'):
        setting.return_value.get.side_effect = {
            'pdns_api_url': 'http://powerdns.test',
            'pdns_api_key': 'test-key',
            'pdns_api_timeout': 5,
            'verify_ssl_connections': False,
        }.get

        result = Domain().add(
            domain_name='catalog-compatibility.example',
            domain_type='native',
            soa_edit_api='DEFAULT',
        )

    assert result['status'] == 'ok'
    assert 'catalog' not in fetch_json.call_args.kwargs['data']


def test_catalog_templates_use_adminlte_4_and_bootstrap_5_markup():
    domain = Path('powerdnsadmin/templates/domain.html').read_text()
    domain_add = Path('powerdnsadmin/templates/domain_add.html').read_text()
    domain_setting = Path(
        'powerdnsadmin/templates/domain_setting.html').read_text()

    assert 'id="catalog-members-card"' in domain
    assert 'id="tbl_catalog_members"' in domain
    assert 'data-bs-toggle="dropdown"' in domain
    assert 'dropdown-menu dropdown-menu-end' in domain
    assert 'class="visually-hidden"' in domain
    assert 'data-toggle="dropdown"' not in domain

    assert 'id="radio_type_producer" value="producer"' in domain_add
    assert 'name="catalog_name" id="selCatalog" class="form-select"' in domain_add
    assert '<strong>Producer</strong>' in domain_add

    assert 'class="card card-outline card-secondary shadow"' in domain_setting
    assert 'class="form-label" for="domain_catalog"' in domain_setting
    assert (
        'name="domain_catalog" id="domain_catalog" class="form-select"'
        in domain_setting
    )
    assert 'name="domain_catalog" class="form-control"' not in domain_setting
