import re
import sys
import json
import requests
import urlparse
import hashlib

from app import app
from certutil import *
from distutils.version import StrictVersion
from datetime import datetime,timedelta
from threading import Thread
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser

idp_timestamp = datetime(1970,1,1)
idp_data = None
if app.config['SAML_ENABLED']:
    idp_data = OneLogin_Saml2_IdPMetadataParser.parse_remote(app.config['SAML_METADATA_URL'])
    if idp_data == None:
        print('SAML: IDP Metadata initial load failed')
        exit(-1)
    idp_timestamp = datetime.now()

def get_idp_data():
    global idp_data, idp_timestamp
    lifetime = timedelta(minutes=app.config['SAML_METADATA_CACHE_LIFETIME'])
    if idp_timestamp+lifetime < datetime.now():
        background_thread = Thread(target=retreive_idp_data)
        background_thread.start()
    return idp_data

def retreive_idp_data():
    global idp_data, idp_timestamp
    new_idp_data = OneLogin_Saml2_IdPMetadataParser.parse_remote(app.config['SAML_METADATA_URL'])
    if new_idp_data != None:
        idp_data = new_idp_data
        idp_timestamp = datetime.now()
        print("SAML: IDP Metadata successfully retreived from: " + app.config['SAML_METADATA_URL'])
    else:
        print("SAML: IDP Metadata could not be retreived")

if 'TIMEOUT' in app.config.keys():
    TIMEOUT = app.config['TIMEOUT']
else:
    TIMEOUT = 10

def auth_from_url(url):
    auth = None
    parsed_url = urlparse.urlparse(url).netloc
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
        raise RuntimeError("While fetching " + remote_url + ": " + str(e)), None, sys.exc_info()[2]

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
        raise Exception("While fetching " + remote_url + ": " + str(e)), None, sys.exc_info()[2]

    # don't use r.json here, as it will read from r.text, which will trigger
    # content encoding auto-detection in almost all cases, WHICH IS EXTREMELY
    # SLOOOOOOOOOOOOOOOOOOOOOOW. just don't.
    data = None
    try:
        data = json.loads(r.content)
    except UnicodeDecodeError:
        data = json.loads(r.content, 'iso-8859-1')
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


    hash_string = hashlib.md5(email).hexdigest()
    return "https://s.gravatar.com/avatar/%s?s=%s" % (hash_string, size)


def prepare_flask_request(request):
    # If server is behind proxys or balancers use the HTTP_X_FORWARDED fields
    url_data = urlparse.urlparse(request.url)
    return {
        'https': 'on' if request.scheme == 'https' else 'off',
        'http_host': request.host,
        'server_port': url_data.port,
        'script_name': request.path,
        'get_data': request.args.copy(),
        'post_data': request.form.copy(),
        # Uncomment if using ADFS as IdP, https://github.com/onelogin/python-saml/pull/144
        'lowercase_urlencoding': True,
        'query_string': request.query_string
    }

def init_saml_auth(req):
    own_url = ''
    if req['https'] == 'on':
        own_url = 'https://'
    else:
        own_url = 'http://'
    own_url += req['http_host']
    metadata = get_idp_data()
    settings = {}
    settings['sp'] = {}
    settings['sp']['NameIDFormat'] = idp_data['sp']['NameIDFormat']
    settings['sp']['entityId'] = app.config['SAML_SP_ENTITY_ID']
    cert = open(CERT_FILE, "r").readlines()
    key = open(KEY_FILE, "r").readlines()
    settings['sp']['privateKey'] = "".join(key)
    settings['sp']['x509cert'] = "".join(cert)
    settings['sp']['assertionConsumerService'] = {}
    settings['sp']['assertionConsumerService']['binding'] = 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'
    settings['sp']['assertionConsumerService']['url'] = own_url+'/saml/authorized'
    settings['sp']['attributeConsumingService'] = {}
    settings['sp']['singleLogoutService'] = {}
    settings['sp']['singleLogoutService']['binding'] = 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
    settings['sp']['singleLogoutService']['url'] = own_url+'/saml/sls'
    settings['idp'] = metadata['idp']
    settings['strict'] = True
    settings['debug'] = app.config['SAML_DEBUG']
    settings['security'] = {}
    settings['security']['digestAlgorithm'] = 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha256'
    settings['security']['metadataCacheDuration'] = None
    settings['security']['metadataValidUntil'] = None
    settings['security']['requestedAuthnContext'] = True
    settings['security']['signatureAlgorithm'] = 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha256'
    settings['security']['wantAssertionsEncrypted'] = False
    settings['security']['wantAttributeStatement'] = True
    settings['security']['wantNameId'] = True
    settings['security']['authnRequestsSigned'] = app.config['SAML_SIGN_REQUEST']
    settings['security']['logoutRequestSigned'] = app.config['SAML_SIGN_REQUEST']
    settings['security']['logoutResponseSigned'] = app.config['SAML_SIGN_REQUEST']
    settings['security']['nameIdEncrypted'] = False
    settings['security']['signMetadata'] = True
    settings['security']['wantAssertionsSigned'] = True
    settings['security']['wantMessagesSigned'] = True
    settings['security']['wantNameIdEncrypted'] = False
    settings['contactPerson'] = {}
    settings['contactPerson']['support'] = {}
    settings['contactPerson']['support']['emailAddress'] = app.config['SAML_SP_CONTACT_NAME']
    settings['contactPerson']['support']['givenName'] = app.config['SAML_SP_CONTACT_MAIL']
    settings['contactPerson']['technical'] = {}
    settings['contactPerson']['technical']['emailAddress'] = app.config['SAML_SP_CONTACT_NAME']
    settings['contactPerson']['technical']['givenName'] = app.config['SAML_SP_CONTACT_MAIL']
    settings['organization'] = {}
    settings['organization']['en-US'] = {}
    settings['organization']['en-US']['displayname'] = 'PowerDNS-Admin'
    settings['organization']['en-US']['name'] = 'PowerDNS-Admin'
    settings['organization']['en-US']['url'] = own_url
    auth = OneLogin_Saml2_Auth(req, settings)
    return auth