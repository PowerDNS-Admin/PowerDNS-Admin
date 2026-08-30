#!/usr/bin/env python3

import http.cookiejar
import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request


FREEIPA_URL = os.environ['FREEIPA_URL'].rstrip('/')
ADMIN_USERNAME = os.environ['FREEIPA_ADMIN_USERNAME']
ADMIN_PASSWORD = os.environ['FREEIPA_ADMIN_PASSWORD']
USER_PASSWORD = os.environ['FREEIPA_USER_PASSWORD']
REFERER = f'{FREEIPA_URL}/ipa'

USERS = {
    'keycloak-bind': ('Keycloak', 'Bind', 'keycloak-bind@example.org'),
    'pda-bind': ('PowerDNS-Admin', 'Bind', 'pda-bind@example.org'),
    'pda-user': ('PowerDNS-Admin', 'User', 'pda-user@example.org'),
    'pda-operator': ('PowerDNS-Admin', 'Operator', 'pda-operator@example.org'),
    'pda-admin': ('PowerDNS-Admin', 'Administrator', 'pda-admin@example.org'),
}

GROUPS = {
    'pda-users': ('PowerDNS-Admin users', ['pda-user']),
    'pda-operators': ('PowerDNS-Admin operators', ['pda-operator']),
    'pda-admins': ('PowerDNS-Admin administrators', ['pda-admin']),
}


def request_opener():
    cookie_jar = http.cookiejar.CookieJar()
    tls_context = ssl.create_default_context()
    tls_context.check_hostname = False
    tls_context.verify_mode = ssl.CERT_NONE
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar),
        urllib.request.HTTPSHandler(context=tls_context),
    )


def authenticate(opener):
    login_data = urllib.parse.urlencode({
        'user': ADMIN_USERNAME,
        'password': ADMIN_PASSWORD,
    }).encode()
    request = urllib.request.Request(
        f'{FREEIPA_URL}/ipa/session/login_password',
        data=login_data,
        headers={
            'Accept': 'text/plain',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': REFERER,
        },
        method='POST',
    )
    with opener.open(request, timeout=30):
        return


def rpc(opener, method, args, options=None, allow_error=False):
    payload = json.dumps({
        'id': 0,
        'method': method,
        'params': [args, options or {}],
    }).encode()
    request = urllib.request.Request(
        f'{FREEIPA_URL}/ipa/session/json',
        data=payload,
        headers={
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Referer': REFERER,
        },
        method='POST',
    )
    with opener.open(request, timeout=30) as response:
        result = json.load(response)
    if result.get('error') and not allow_error:
        raise RuntimeError(f'{method} failed: {result["error"]}')
    return result


def exists(opener, object_type, name):
    return rpc(opener, f'{object_type}_show', [name], allow_error=True).get(
        'error') is None


def seed(opener):
    for username, (first_name, last_name, email) in USERS.items():
        if exists(opener, 'user', username):
            print(f'FreeIPA user {username} already exists')
            continue
        rpc(opener, 'user_add', [username], {
            'givenname': first_name,
            'sn': last_name,
            'mail': email,
            'userpassword': USER_PASSWORD,
            'krbpasswordexpiration': '20380119031407Z',
        })
        print(f'Created FreeIPA user {username}')

    for group_name, (description, members) in GROUPS.items():
        if not exists(opener, 'group', group_name):
            rpc(opener, 'group_add', [group_name], {
                'description': description,
            })
            print(f'Created FreeIPA group {group_name}')
        result = rpc(opener, 'group_add_member', [group_name], {
            'user': members,
        })
        failed = result['result'].get('failed', {}).get('member', {}).get(
            'user', [])
        unexpected = [failure for failure in failed
                      if 'already a member' not in str(failure)]
        if unexpected:
            raise RuntimeError(
                f'Failed to add members to {group_name}: {unexpected}')
        print(f'Ensured FreeIPA group membership for {group_name}')


def main():
    opener = request_opener()
    for attempt in range(60):
        try:
            authenticate(opener)
            break
        except (OSError, urllib.error.URLError) as error:
            if attempt == 59:
                raise
            print(f'Waiting for FreeIPA API: {error}')
            time.sleep(5)
    seed(opener)


if __name__ == '__main__':
    main()
