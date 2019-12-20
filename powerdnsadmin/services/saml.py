from datetime import datetime, timedelta
from threading import Thread
from flask import current_app
import json
import os

from ..lib.certutil import KEY_FILE, CERT_FILE, create_self_signed_cert
from ..lib.utils import urlparse


class SAML(object):
    def __init__(self):
        if current_app.config['SAML_ENABLED']:
            from onelogin.saml2.auth import OneLogin_Saml2_Auth
            from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser

            self.idp_timestamp = datetime.now()
            self.OneLogin_Saml2_Auth = OneLogin_Saml2_Auth
            self.OneLogin_Saml2_IdPMetadataParser = OneLogin_Saml2_IdPMetadataParser
            self.idp_data = None

            if 'SAML_IDP_ENTITY_ID' in current_app.config:
                self.idp_data = OneLogin_Saml2_IdPMetadataParser.parse_remote(
                    current_app.config['SAML_METADATA_URL'],
                    entity_id=current_app.config.get('SAML_IDP_ENTITY_ID',
                                                     None),
                    required_sso_binding=current_app.
                    config['SAML_IDP_SSO_BINDING'])
            else:
                self.idp_data = OneLogin_Saml2_IdPMetadataParser.parse_remote(
                    current_app.config['SAML_METADATA_URL'],
                    entity_id=current_app.config.get('SAML_IDP_ENTITY_ID',
                                                     None))
            if self.idp_data is None:
                current_app.logger.info(
                    'SAML: IDP Metadata initial load failed')
                exit(-1)

    def get_idp_data(self):

        lifetime = timedelta(
            minutes=current_app.config['SAML_METADATA_CACHE_LIFETIME'])

        if self.idp_timestamp + lifetime < datetime.now():
            background_thread = Thread(target=self.retrieve_idp_data())
            background_thread.start()

        return self.idp_data

    def retrieve_idp_data(self):

        if 'SAML_IDP_SSO_BINDING' in current_app.config:
            new_idp_data = self.OneLogin_Saml2_IdPMetadataParser.parse_remote(
                current_app.config['SAML_METADATA_URL'],
                entity_id=current_app.config.get('SAML_IDP_ENTITY_ID', None),
                required_sso_binding=current_app.config['SAML_IDP_SSO_BINDING']
            )
        else:
            new_idp_data = self.OneLogin_Saml2_IdPMetadataParser.parse_remote(
                current_app.config['SAML_METADATA_URL'],
                entity_id=current_app.config.get('SAML_IDP_ENTITY_ID', None))
        if new_idp_data is not None:
            self.idp_data = new_idp_data
            self.idp_timestamp = datetime.now()
            current_app.logger.info(
                "SAML: IDP Metadata successfully retrieved from: " +
                current_app.config['SAML_METADATA_URL'])
        else:
            current_app.logger.info(
                "SAML: IDP Metadata could not be retrieved")

    def prepare_flask_request(self, request):
        # If server is behind proxys or balancers use the HTTP_X_FORWARDED fields
        url_data = urlparse(request.url)
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

    def init_saml_auth(self, req):
        own_url = ''
        if req['https'] == 'on':
            own_url = 'https://'
        else:
            own_url = 'http://'
        own_url += req['http_host']
        metadata = self.get_idp_data()
        settings = {}
        settings['sp'] = {}
        if 'SAML_NAMEID_FORMAT' in current_app.config:
            settings['sp']['NameIDFormat'] = current_app.config[
                'SAML_NAMEID_FORMAT']
        else:
            settings['sp']['NameIDFormat'] = self.idp_data.get('sp', {}).get(
                'NameIDFormat',
                'urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified')
        settings['sp']['entityId'] = current_app.config['SAML_SP_ENTITY_ID']


        if ('SAML_CERT_FILE' in current_app.config) and ('SAML_KEY_FILE' in current_app.config):

             saml_cert_file = current_app.config['SAML_CERT_FILE']
             saml_key_file = current_app.config['SAML_KEY_FILE']

             if os.path.isfile(saml_cert_file):
                 cert = open(saml_cert_file, "r").readlines()
                 settings['sp']['x509cert'] = "".join(cert)
             if os.path.isfile(saml_key_file):
                 key = open(saml_key_file, "r").readlines()
                 settings['sp']['privateKey'] = "".join(key)

        else:

            if (os.path.isfile(CERT_FILE)) and (os.path.isfile(KEY_FILE)):
                 cert = open(CERT_FILE, "r").readlines()
                 key = open(KEY_FILE, "r").readlines()
            else:
                 create_self_signed_cert()
                 cert = open(CERT_FILE, "r").readlines()
                 key = open(KEY_FILE, "r").readlines()

            settings['sp']['x509cert'] = "".join(cert)
            settings['sp']['privateKey'] = "".join(key) 


        if 'SAML_SP_REQUESTED_ATTRIBUTES' in current_app.config:
             saml_req_attr = json.loads(current_app.config['SAML_SP_REQUESTED_ATTRIBUTES'])
             settings['sp']['attributeConsumingService'] = {
                "serviceName": "PowerDNSAdmin",
                "serviceDescription": "PowerDNS-Admin - PowerDNS administration utility",
                "requestedAttributes": saml_req_attr
             }
        else:
             settings['sp']['attributeConsumingService'] = {}


        settings['sp']['assertionConsumerService'] = {}
        settings['sp']['assertionConsumerService'][
            'binding'] = 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'
        settings['sp']['assertionConsumerService'][
            'url'] = own_url + '/saml/authorized'
        settings['sp']['singleLogoutService'] = {}
        settings['sp']['singleLogoutService'][
            'binding'] = 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
        settings['sp']['singleLogoutService']['url'] = own_url + '/saml/sls'
        settings['idp'] = metadata['idp']
        settings['strict'] = True
        settings['debug'] = current_app.config['SAML_DEBUG']
        settings['security'] = {}
        settings['security'][
            'digestAlgorithm'] = 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha256'
        settings['security']['metadataCacheDuration'] = None
        settings['security']['metadataValidUntil'] = None
        settings['security']['requestedAuthnContext'] = True
        settings['security'][
            'signatureAlgorithm'] = 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha256'
        settings['security']['wantAssertionsEncrypted'] = True
        settings['security']['wantAttributeStatement'] = True
        settings['security']['wantNameId'] = True
        settings['security']['authnRequestsSigned'] = current_app.config[
            'SAML_SIGN_REQUEST']
        settings['security']['logoutRequestSigned'] = current_app.config[
            'SAML_SIGN_REQUEST']
        settings['security']['logoutResponseSigned'] = current_app.config[
            'SAML_SIGN_REQUEST']
        settings['security']['nameIdEncrypted'] = False
        settings['security']['signMetadata'] = True
        settings['security']['wantAssertionsSigned'] = True
        settings['security']['wantMessagesSigned'] = current_app.config.get(
            'SAML_WANT_MESSAGE_SIGNED', True)
        settings['security']['wantNameIdEncrypted'] = False
        settings['contactPerson'] = {}
        settings['contactPerson']['support'] = {}
        settings['contactPerson']['support'][
            'emailAddress'] = current_app.config['SAML_SP_CONTACT_NAME']
        settings['contactPerson']['support']['givenName'] = current_app.config[
            'SAML_SP_CONTACT_MAIL']
        settings['contactPerson']['technical'] = {}
        settings['contactPerson']['technical'][
            'emailAddress'] = current_app.config['SAML_SP_CONTACT_MAIL']
        settings['contactPerson']['technical'][
            'givenName'] = current_app.config['SAML_SP_CONTACT_NAME']
        settings['organization'] = {}
        settings['organization']['en-US'] = {}
        settings['organization']['en-US']['displayname'] = 'PowerDNS-Admin'
        settings['organization']['en-US']['name'] = 'PowerDNS-Admin'
        settings['organization']['en-US']['url'] = own_url
        auth = self.OneLogin_Saml2_Auth(req, settings)
        return auth
