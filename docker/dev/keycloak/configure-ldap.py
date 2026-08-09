#!/usr/bin/env python3

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request


KEYCLOAK_URL = os.environ['KEYCLOAK_URL'].rstrip('/')
ADMIN_USERNAME = os.environ['KEYCLOAK_ADMIN_USERNAME']
ADMIN_PASSWORD = os.environ['KEYCLOAK_ADMIN_PASSWORD']
REALM = os.environ['KEYCLOAK_REALM']
OIDC_CLIENT_ID = os.environ['KEYCLOAK_OIDC_CLIENT_ID']
SAML_CLIENT_ID = os.environ['KEYCLOAK_SAML_CLIENT_ID']
LDAP_URL = os.environ['KEYCLOAK_LDAP_URL']
LDAP_USERS_DN = os.environ['KEYCLOAK_LDAP_USERS_DN']
LDAP_GROUPS_DN = os.environ['KEYCLOAK_LDAP_GROUPS_DN']
LDAP_BIND_DN = os.environ['KEYCLOAK_LDAP_BIND_DN']
LDAP_BIND_PASSWORD = os.environ['KEYCLOAK_LDAP_BIND_PASSWORD']
LDAP_VENDOR = os.environ.get('KEYCLOAK_LDAP_VENDOR', 'other')
LDAP_UUID_ATTRIBUTE = os.environ.get('KEYCLOAK_LDAP_UUID_ATTRIBUTE', 'entryUUID')
LDAP_PROVIDER_NAME = os.environ.get('KEYCLOAK_LDAP_PROVIDER_NAME', 'ldap')
LDAP_USER_SEARCH_FILTER = os.environ['KEYCLOAK_LDAP_USER_SEARCH_FILTER']
LDAP_GROUP_FILTER = os.environ.get(
    'KEYCLOAK_LDAP_GROUP_FILTER',
    '(|(cn=pda-users)(cn=pda-operators)(cn=pda-admins))',
)
LDAP_SEARCH_SCOPE = os.environ.get('KEYCLOAK_LDAP_SEARCH_SCOPE', '1')


def request(method, path, token=None, payload=None, form=None):
    headers = {'Accept': 'application/json'}
    data = None
    if token:
        headers['Authorization'] = f'Bearer {token}'
    if payload is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(payload).encode()
    elif form is not None:
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        data = urllib.parse.urlencode(form).encode()
    api_request = urllib.request.Request(
        f'{KEYCLOAK_URL}{path}',
        data=data,
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(api_request, timeout=30) as response:
        body = response.read()
        return json.loads(body) if body else None


def admin_token():
    token_response = request('POST',
                             '/realms/master/protocol/openid-connect/token',
                             form={
                                 'client_id': 'admin-cli',
                                 'grant_type': 'password',
                                 'username': ADMIN_USERNAME,
                                 'password': ADMIN_PASSWORD,
                             })
    return token_response['access_token']


def wait_for_keycloak():
    for attempt in range(120):
        try:
            return admin_token()
        except (OSError, urllib.error.HTTPError, urllib.error.URLError) as error:
            if attempt == 119:
                raise
            print(f'Waiting for Keycloak Admin API: {error}')
            time.sleep(5)


def ldap_component(realm_id):
    return {
        'name': LDAP_PROVIDER_NAME,
        'providerId': 'ldap',
        'providerType': 'org.keycloak.storage.UserStorageProvider',
        'parentId': realm_id,
        'config': {
            'enabled': ['true'],
            'priority': ['0'],
            'fullSyncPeriod': ['-1'],
            'changedSyncPeriod': ['-1'],
            'cachePolicy': ['DEFAULT'],
            'batchSizeForSync': ['1000'],
            'editMode': ['READ_ONLY'],
            'importEnabled': ['true'],
            'syncRegistrations': ['false'],
            'vendor': [LDAP_VENDOR],
            'usernameLDAPAttribute': ['uid'],
            'rdnLDAPAttribute': ['uid'],
            'uuidLDAPAttribute': [LDAP_UUID_ATTRIBUTE],
            'userObjectClasses': ['inetOrgPerson, organizationalPerson'],
            'connectionUrl': [LDAP_URL],
            'usersDn': [LDAP_USERS_DN],
            'authType': ['simple'],
            'bindDn': [LDAP_BIND_DN],
            'bindCredential': [LDAP_BIND_PASSWORD],
            'customUserSearchFilter': [LDAP_USER_SEARCH_FILTER],
            'searchScope': [LDAP_SEARCH_SCOPE],
            'useTruststoreSpi': ['ldapsOnly'],
            'connectionPooling': ['true'],
            'pagination': ['true'],
            'trustEmail': ['true'],
        },
    }


def ldap_group_component(parent_id):
    return {
        'name': f'{LDAP_PROVIDER_NAME}-groups',
        'providerId': 'group-ldap-mapper',
        'providerType': (
            'org.keycloak.storage.ldap.mappers.LDAPStorageMapper'),
        'parentId': parent_id,
        'config': {
            'groups.dn': [LDAP_GROUPS_DN],
            'group.name.ldap.attribute': ['cn'],
            'group.object.classes': ['groupOfNames'],
            'preserve.group.inheritance': ['false'],
            'membership.ldap.attribute': ['member'],
            'membership.attribute.type': ['DN'],
            'membership.user.ldap.attribute': ['uid'],
            'groups.ldap.filter': [LDAP_GROUP_FILTER],
            'mode': ['LDAP_ONLY'],
            'user.roles.retrieve.strategy': [
                'LOAD_GROUPS_BY_MEMBER_ATTRIBUTE',
            ],
            'drop.non.existing.groups.during.sync': ['false'],
        },
    }


def find_client(token, client_id):
    query = urllib.parse.urlencode({'clientId': client_id})
    clients = request(
        'GET', f'/admin/realms/{REALM}/clients?{query}', token=token)
    if len(clients) != 1:
        raise RuntimeError(
            f'Expected one Keycloak client named {client_id}, got {len(clients)}')
    return clients[0]['id']


def configure_oidc_client(token):
    client_id = find_client(token, OIDC_CLIENT_ID)
    client = request(
        'GET', f'/admin/realms/{REALM}/clients/{client_id}', token=token)
    client['redirectUris'] = [
        'http://localhost:9191/oidc/authorized',
        'https://localhost:9191/oidc/authorized',
    ]
    client['webOrigins'] = [
        'http://localhost:9191',
        'https://localhost:9191',
    ]
    client.setdefault('attributes', {})['post.logout.redirect.uris'] = (
        'http://localhost:9191/*##https://localhost:9191/*')
    request('PUT',
            f'/admin/realms/{REALM}/clients/{client_id}',
            token=token,
            payload=client)
    print('Ensured Keycloak OIDC client HTTP and HTTPS redirect URLs')


def saml_protocol_mappers():
    attributes = [
        ('username', 'username'),
        ('email', 'email'),
        ('givenname', 'firstName'),
        ('surname', 'lastName'),
    ]
    mappers = []
    for attribute_name, user_property in attributes:
        mappers.append({
            'name': attribute_name,
            'protocol': 'saml',
            'protocolMapper': 'saml-user-property-mapper',
            'consentRequired': False,
            'config': {
                'user.attribute': user_property,
                'attribute.name': attribute_name,
                'attribute.nameformat': 'Basic',
                'friendly.name': attribute_name,
            },
        })
    mappers.append({
        'name': 'groups',
        'protocol': 'saml',
        'protocolMapper': 'saml-group-membership-mapper',
        'consentRequired': False,
        'config': {
            'attribute.name': 'groups',
            'full.path': 'false',
            # single=true => one Attribute with many values; false repeats Name
            # and python3-saml rejects that under strict mode.
            'single': 'true',
        },
    })
    return mappers


def saml_client():
    return {
        'clientId': SAML_CLIENT_ID,
        'name': 'PowerDNS-Admin SAML',
        'enabled': True,
        'protocol': 'saml',
        'baseUrl': 'http://localhost:9191',
        'frontchannelLogout': True,
        'fullScopeAllowed': True,
        # Drop Keycloak's default role_list scope: with single=false it emits
        # one Attribute Name="Role" per role, which python3-saml rejects.
        'defaultClientScopes': [],
        'optionalClientScopes': [],
        'redirectUris': [
            'http://localhost:9191/saml/authorized',
            'https://localhost:9191/saml/authorized',
        ],
        'attributes': {
            'saml.authnstatement': 'true',
            'saml.assertion.signature': 'true',
            'saml.client.signature': 'false',
            'saml.encrypt': 'false',
            'saml.force.post.binding': 'true',
            'saml.multivalued.roles': 'true',
            'saml.onetimeuse.condition': 'false',
            'saml.server.signature': 'true',
            'saml.server.signature.keyinfo.ext': 'false',
            'saml.signature.algorithm': 'RSA_SHA256',
            'saml_name_id_format': 'username',
            'saml_assertion_consumer_url_post': (
                'http://localhost:9191/saml/authorized'),
            'saml_single_logout_service_url_redirect': (
                'http://localhost:9191/saml/sls'),
        },
        'protocolMappers': saml_protocol_mappers(),
    }


def remove_default_client_scopes(token, client_id):
    """Ensure the SAML client does not inherit role_list (duplicate Role attrs)."""
    scopes = request(
        'GET',
        f'/admin/realms/{REALM}/clients/{client_id}/default-client-scopes',
        token=token,
    ) or []
    for scope in scopes:
        request(
            'DELETE',
            f'/admin/realms/{REALM}/clients/{client_id}'
            f'/default-client-scopes/{scope["id"]}',
            token=token,
        )
    if scopes:
        print(
            'Removed default SAML client scopes: '
            + ', '.join(scope['name'] for scope in scopes)
        )


def configure_saml_client(token):
    query = urllib.parse.urlencode({'clientId': SAML_CLIENT_ID})
    clients = request(
        'GET', f'/admin/realms/{REALM}/clients?{query}', token=token)
    representation = saml_client()
    if clients:
        client_id = clients[0]['id']
        existing = request(
            'GET', f'/admin/realms/{REALM}/clients/{client_id}', token=token)
        representation['id'] = client_id
        representation['protocolMappers'] = existing.get(
            'protocolMappers', [])
        request('PUT',
                f'/admin/realms/{REALM}/clients/{client_id}',
                token=token,
                payload=representation)
        desired_mappers = saml_protocol_mappers()
        existing_by_name = {
            mapper['name']: mapper
            for mapper in representation['protocolMappers']
        }
        for mapper in desired_mappers:
            existing_mapper = existing_by_name.get(mapper['name'])
            if existing_mapper:
                mapper['id'] = existing_mapper['id']
                request(
                    'PUT',
                    f'/admin/realms/{REALM}/clients/{client_id}'
                    f'/protocol-mappers/models/{existing_mapper["id"]}',
                    token=token,
                    payload=mapper)
            else:
                request(
                    'POST',
                    f'/admin/realms/{REALM}/clients/{client_id}'
                    '/protocol-mappers/models',
                    token=token,
                    payload=mapper)
        remove_default_client_scopes(token, client_id)
        print('Updated Keycloak SAML client and attribute mappers')
    else:
        request('POST',
                f'/admin/realms/{REALM}/clients',
                token=token,
                payload=representation)
        clients = request(
            'GET', f'/admin/realms/{REALM}/clients?{query}', token=token)
        remove_default_client_scopes(token, clients[0]['id'])
        print('Created Keycloak SAML client and attribute mappers')


def list_ldap_providers(token):
    query = urllib.parse.urlencode({
        'type': 'org.keycloak.storage.UserStorageProvider',
    })
    components = request(
        'GET', f'/admin/realms/{REALM}/components?{query}', token=token) or []
    return [
        component for component in components
        if component.get('providerId') == 'ldap'
    ]


def remove_stale_ldap_providers(token):
    """Drop LDAP providers left from the other identity backend.

    Switching between OpenLDAP and FreeIPA without wiping the Keycloak MySQL
    volume otherwise leaves a dead federation target (for example
    ldap://ipa.example.org) that breaks user import and login.
    """
    for component in list_ldap_providers(token):
        if component.get('name') == LDAP_PROVIDER_NAME:
            continue
        request(
            'DELETE',
            f'/admin/realms/{REALM}/components/{component["id"]}',
            token=token)
        print(
            f'Removed stale Keycloak LDAP provider {component.get("name")!r}')


def sync_ldap_users(token, component_id):
    sync_query = urllib.parse.urlencode({'action': 'triggerFullSync'})
    request(
        'POST',
        f'/admin/realms/{REALM}/user-storage/{component_id}/sync?{sync_query}',
        token=token)
    print(f'Triggered full user sync for {LDAP_PROVIDER_NAME}')


def configure_group_mapper(token, parent_id):
    component = ldap_group_component(parent_id)
    query = urllib.parse.urlencode({'parent': parent_id})
    children = request(
        'GET', f'/admin/realms/{REALM}/components?{query}', token=token)
    existing = [
        child for child in children
        if child.get('name') == component['name']
        and child.get('providerId') == component['providerId']
    ]
    if existing:
        mapper_id = existing[0]['id']
        component['id'] = mapper_id
        request('PUT',
                f'/admin/realms/{REALM}/components/{mapper_id}',
                token=token,
                payload=component)
        print(f'Updated Keycloak {LDAP_PROVIDER_NAME} group mapper')
    else:
        request('POST',
                f'/admin/realms/{REALM}/components',
                token=token,
                payload=component)
        children = request(
            'GET', f'/admin/realms/{REALM}/components?{query}', token=token)
        existing = [
            child for child in children
            if child.get('name') == component['name']
            and child.get('providerId') == component['providerId']
        ]
        if not existing:
            raise RuntimeError('Keycloak did not create the LDAP group mapper')
        mapper_id = existing[0]['id']
        print(f'Created Keycloak {LDAP_PROVIDER_NAME} group mapper')

    sync_query = urllib.parse.urlencode({'direction': 'fedToKeycloak'})
    request(
        'POST',
        f'/admin/realms/{REALM}/user-storage/{parent_id}'
        f'/mappers/{mapper_id}/sync?{sync_query}',
        token=token)
    print(f'Synchronized {LDAP_PROVIDER_NAME} role groups into Keycloak')


def main():
    token = wait_for_keycloak()
    realm = request('GET', f'/admin/realms/{REALM}', token=token)
    configure_oidc_client(token)
    configure_saml_client(token)
    remove_stale_ldap_providers(token)
    component = ldap_component(realm['id'])
    query = urllib.parse.urlencode({
        'name': LDAP_PROVIDER_NAME,
        'type': 'org.keycloak.storage.UserStorageProvider',
    })
    existing = request(
        'GET', f'/admin/realms/{REALM}/components?{query}', token=token)
    if existing:
        component_id = existing[0]['id']
        component['id'] = component_id
        request('PUT',
                f'/admin/realms/{REALM}/components/{component_id}',
                token=token,
                payload=component)
        print(f'Updated Keycloak {LDAP_PROVIDER_NAME} user federation provider')
    else:
        request('POST',
                f'/admin/realms/{REALM}/components',
                token=token,
                payload=component)
        existing = request(
            'GET', f'/admin/realms/{REALM}/components?{query}', token=token)
        if not existing:
            raise RuntimeError('Keycloak did not create the LDAP provider')
        component_id = existing[0]['id']
        print(f'Created Keycloak {LDAP_PROVIDER_NAME} user federation provider')

    configure_group_mapper(token, component_id)
    sync_ldap_users(token, component_id)

    users_query = urllib.parse.urlencode({
        'username': 'pda-user',
        'exact': 'true',
    })
    users = request('GET',
                    f'/admin/realms/{REALM}/users?{users_query}',
                    token=token)
    if not users or users[0].get('federationLink') != component_id:
        raise RuntimeError(
            f'Keycloak could not import pda-user from {LDAP_PROVIDER_NAME}')
    print(f'Imported pda-user from {LDAP_PROVIDER_NAME} into the pda-dev realm')

    user_groups = request(
        'GET',
        f'/admin/realms/{REALM}/users/{users[0]["id"]}/groups',
        token=token)
    if 'pda-users' not in {group['name'] for group in user_groups}:
        raise RuntimeError(
            'Keycloak could not resolve pda-user group membership')
    print(
        f'Resolved pda-user {LDAP_PROVIDER_NAME} group membership in Keycloak')


if __name__ == '__main__':
    main()
