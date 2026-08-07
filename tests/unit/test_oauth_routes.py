def test_oauth_callbacks_are_registered_during_application_setup(app):
    callback_endpoints = {
        rule.rule: rule.endpoint
        for rule in app.url_map.iter_rules()
        if rule.rule.endswith('/authorized')
    }

    assert callback_endpoints['/google/authorized'] == \
        'index.google_authorized'
    assert callback_endpoints['/github/authorized'] == \
        'index.github_authorized'
    assert callback_endpoints['/azure/authorized'] == \
        'index.azure_authorized'
    assert callback_endpoints['/oidc/authorized'] == \
        'index.oidc_authorized'
