import re
import sys
import json
import requests
import hashlib

from app import app
from distutils.version import StrictVersion
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

if 'TIMEOUT' in list(app.config.keys()):
    TIMEOUT = app.config['TIMEOUT']
else:
    TIMEOUT = 10

def auth_from_url(url):
    auth = None
    parsed_url = urlparse(url).netloc
    if '@' in parsed_url:
        auth = parsed_url.split('@')[0].split(':')
        auth = requests.auth.HTTPBasicAuth(auth[0], auth[1])
    return auth


def fetch_remote(remote_url, method='GET', data=None, accept=None, params=None, timeout=None, headers=None):
    if data is not None and type(data) != str:
        data = json.dumps(data)

    if timeout is None:
        timeout = TIMEOUT

    verify = False

    our_headers = {
        'user-agent': 'powerdnsadmin/0',
        'pragma': 'no-cache',
        'cache-control': 'no-cache'
    }
    if accept is not None:
        our_headers['accept'] = accept
    if headers is not None:
        our_headers.update(headers)

    r = requests.request(
        method,
        remote_url,
        headers=headers,
        verify=verify,
        auth=auth_from_url(remote_url),
        timeout=timeout,
        data=data,
        params=params
        )
    try:
        if r.status_code not in (200, 400, 422):
            r.raise_for_status()
    except Exception as e:
        raise RuntimeError("While fetching %s: %s" % (remote_url, str(e)))

    return r


def fetch_json(remote_url, method='GET', data=None, params=None, headers=None):
    r = fetch_remote(remote_url, method=method, data=data, params=params, headers=headers, accept='application/json; q=1')

    if method == "DELETE":
        return True

    if r.status_code == 204:
        return {}

    try:
        assert('json' in r.headers['content-type'])
    except Exception as e:
        raise Exception("While fetching %s: %s" % (remote_url, str(e)))

    data = r.json()
    return data


def display_record_name(data):
    record_name, domain_name = data
    if record_name == domain_name:
        return '@'
    else:
        return record_name.replace('.'+domain_name, '')

def display_master_name(data):
    """
    input data: "[u'127.0.0.1', u'8.8.8.8']"
    """
    matches = re.findall(r'\'(.+?)\'', data)
    return ", ".join(matches)

def display_time(amount, units='s', remove_seconds=True):
    """
    Convert timestamp to normal time format
    """
    amount = int(amount)
    INTERVALS = [(lambda mlsec:divmod(mlsec, 1000), 'ms'),
                 (lambda seconds:divmod(seconds, 60), 's'),
                 (lambda minutes:divmod(minutes, 60), 'm'),
                 (lambda hours:divmod(hours, 24), 'h'),
                 (lambda days:divmod(days, 7), 'D'),
                 (lambda weeks:divmod(weeks, 4), 'W'),
                 (lambda years:divmod(years, 12), 'M'),
                 (lambda decades:divmod(decades, 10), 'Y')]

    for index_start, (interval, unit) in enumerate(INTERVALS):
        if unit == units:
            break

    amount_abrev = []
    last_index = 0
    amount_temp = amount
    for index, (formula, abrev) in enumerate(INTERVALS[index_start: len(INTERVALS)]):
        divmod_result = formula(amount_temp)
        amount_temp = divmod_result[0]
        amount_abrev.append((divmod_result[1], abrev))
        if divmod_result[1] > 0:
            last_index = index
    amount_abrev_partial = amount_abrev[0: last_index + 1]
    amount_abrev_partial.reverse()

    final_string = ''
    for amount, abrev in amount_abrev_partial:
        final_string += str(amount) + abrev + ' '

    if remove_seconds and 'm' in final_string:
        final_string = final_string[:final_string.rfind(' ')]
        return final_string[:final_string.rfind(' ')]

    return final_string

def pdns_api_extended_uri(version):
    """
    Check the pdns version
    """
    if StrictVersion(version) >= StrictVersion('4.0.0'):
        return "/api/v1"
    else:
        return ""

def email_to_gravatar_url(email, size=100):
    """
    AD doesn't necessarily have email
    """

    if not email:
        email=""


    hash_string = hashlib.md5(email.encode('utf-8')).hexdigest()
    return "https://s.gravatar.com/avatar/%s?s=%s" % (hash_string, size)
