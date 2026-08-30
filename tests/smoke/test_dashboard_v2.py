def test_dashboard_v2_domains_json_without_refresh(logged_in_admin_client):
    response = logged_in_admin_client.get(
        '/dashboard/v2/domains/forward?length=10&start=0&draw=1')
    payload = response.get_json()

    assert response.status_code == 200
    assert payload['draw'] == 1
    assert payload['recordsTotal'] == 0
    assert payload['recordsFiltered'] == 0
    assert payload['data'] == []
