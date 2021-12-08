from datetime import datetime, timedelta
from threading import Thread
from flask import current_app
import json
import os

from ..lib.certutil import KEY_FILE, CERT_FILE, create_self_signed_cert
from ..lib.utils import urlparse
from ..models.setting import Setting


class SAML(object):
    def __init__(self):
        if Setting().get('saml_enabled'):
            from onelogin.saml2.auth import OneLogin_Saml2_Auth
            from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser

            self.idp_timestamp = datetime.now()
            self.OneLogin_Saml2_Auth = OneLogin_Saml2_Auth
            self.OneLogin_Saml2_IdPMetadataParser = OneLogin_Saml2_IdPMetadataParser
            self.idp_data = None

            if Setting().get('saml_idp_entity_id'):
                try:
                    self.idp_data = OneLogin_Saml2_IdPMetadataParser.parse_remote(
                        Setting().get('saml_metadata_url'),
                        entity_id=Setting().get('saml_idp_entity_id'),
                        required_sso_binding=Setting().get('saml_idp_sso_binding'))
                except:
                    self.idp_data = None
            else:
                try:
                    self.idp_data = OneLogin_Saml2_IdPMetadataParser.parse_remote(
                        Setting().get('saml_metadata_url'),
                        entity_id=None)
                except:
                    self.idp_data = None
            if self.idp_data is None:
                current_app.logger.info(
                    'SAML: IDP Metadata initial load failed')
                Setting().set('saml_enabled', False)
                print("SAML EN1 ", Setting().get('saml_enabled'))
                # exit(-1)

    def get_idp_data(self):

        # lifetime = timedelta(
        #     minutes=int(Setting().get('saml_metadata_cache_lifetime')))     # should be seconds instead of minutes?
        # Since SAML is now user-configurable, idp_data may change before the lifetime has ended,
        # so metadata should not be cached at all, or outdated settings may be used. 
        try:
            self.retrieve_idp_data()
        except:
            return None
        # if self.idp_timestamp + lifetime < datetime.now():
        background_thread = Thread(target=self.retrieve_idp_data())
        background_thread.start()

        return self.idp_data

    def retrieve_idp_data(self):

        if Setting().get('saml_idp_sso_binding'):
            try:
                new_idp_data = self.OneLogin_Saml2_IdPMetadataParser.parse_remote(
                    Setting().get('saml_metadata_url'),
                    entity_id=Setting().get('saml_idp_entity_id'),
                    required_sso_binding=Setting().get('saml_idp_sso_binding'))
            except:
                new_idp_data = None
        else:
            try:
                new_idp_data = self.OneLogin_Saml2_IdPMetadataParser.parse_remote(
                    Setting().get('saml_metadata_url'),
                    entity_id=Setting().get('saml_idp_entity_id'))
            except:
                new_idp_data = None
        if new_idp_data is not None:
            self.idp_data = new_idp_data
            self.idp_timestamp = datetime.now()
            current_app.logger.info(
                "SAML: IDP Metadata successfully retrieved from: " +
                Setting().get('saml_metadata_url'))
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
        if Setting().get('saml_nameid_format'):
            settings['sp']['NameIDFormat'] = Setting().get('saml_nameid_format')
        else:
            settings['sp']['NameIDFormat'] = self.idp_data.get('sp', {}).get(
                'NameIDFormat',
                'urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified')
        settings['sp']['entityId'] = Setting().get('saml_sp_entity_id')


        if (Setting().get('saml_cert_file')) and (Setting().get('saml_cert_key')):

             saml_cert_file = Setting().get('saml_cert_file')
             saml_key_file = Setting().get('saml_cert_key')

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


        if Setting().get('saml_sp_requested_attributes'):
             saml_req_attr = json.loads(Setting().get('saml_sp_requested_attributes'))
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
        settings['debug'] = Setting().get('saml_debug')
        settings['security'] = {}
        settings['security'][
            'digestAlgorithm'] = Setting().get('saml_digest_algorithm')
        settings['security']['metadataCacheDuration'] = None
        settings['security']['metadataValidUntil'] = None
        settings['security']['requestedAuthnContext'] = True
        settings['security'][
            'signatureAlgorithm'] = Setting.get('saml_signature_algorithm')
        settings['security']['wantAssertionsEncrypted'] = Setting().get('saml_assertion_encrypted')
        settings['security']['wantAttributeStatement'] = True
        settings['security']['wantNameId'] = True
        settings['security']['authnRequestsSigned'] = Setting().get('saml_sign_request')
        settings['security']['logoutRequestSigned'] = Setting().get('saml_sign_request')
        settings['security']['logoutResponseSigned'] = Setting().get('saml_sign_request')
        settings['security']['nameIdEncrypted'] = False
        settings['security']['signMetadata'] = Setting().get('saml_sign_metadata')
        settings['security']['wantAssertionsSigned'] = Setting().get('saml_want_assertions_signed')
        settings['security']['wantMessagesSigned'] = Setting().get('saml_want_message_signed')
        settings['security']['wantNameIdEncrypted'] = False
        settings['contactPerson'] = {}
        settings['contactPerson']['support'] = {}
        settings['contactPerson']['support']['emailAddress'] = Setting().get('saml_sp_contact_mail')
        settings['contactPerson']['support']['givenName'] = Setting().get('saml_sp_contact_name')
        settings['contactPerson']['technical'] = {}
        settings['contactPerson']['technical']['emailAddress'] = Setting().get('saml_sp_contact_mail')
        settings['contactPerson']['technical']['givenName'] = Setting().get('saml_sp_contact_name')
        settings['organization'] = {}
        settings['organization']['en-US'] = {}
        settings['organization']['en-US']['displayname'] = 'PowerDNS-Admin'
        settings['organization']['en-US']['name'] = 'PowerDNS-Admin'
        settings['organization']['en-US']['url'] = own_url
        auth = self.OneLogin_Saml2_Auth(req, settings)
        return auth
