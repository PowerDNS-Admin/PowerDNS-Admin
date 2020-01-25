import traceback
from flask import current_app
from urllib.parse import urljoin

from ..lib import utils
from .setting import Setting


class Server(object):
    """
    This is not a model, it's just an object
    which be assigned data from PowerDNS API
    """
    def __init__(self, server_id=None, server_config=None):
        self.server_id = server_id
        self.server_config = server_config
        # PDNS configs
        self.PDNS_STATS_URL = Setting().get('pdns_api_url')
        self.PDNS_API_KEY = Setting().get('pdns_api_key')
        self.PDNS_VERSION = Setting().get('pdns_version')
        self.API_EXTENDED_URL = utils.pdns_api_extended_uri(self.PDNS_VERSION)

    def get_config(self):
        """
        Get server config
        """
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY

        try:
            jdata = utils.fetch_json(urljoin(
                self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                '/servers/{0}/config'.format(self.server_id)),
                                     headers=headers,
                                     timeout=int(Setting().get('pdns_api_timeout')),
                                     method='GET',
                                     verify=Setting().get('verify_ssl_connections'))
            return jdata
        except Exception as e:
            current_app.logger.error(
                "Can not get server configuration. DETAIL: {0}".format(e))
            current_app.logger.debug(traceback.format_exc())
            return []

    def get_statistic(self):
        """
        Get server statistics
        """
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY

        try:
            jdata = utils.fetch_json(urljoin(
                self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                '/servers/{0}/statistics'.format(self.server_id)),
                                     headers=headers,
                                     timeout=int(Setting().get('pdns_api_timeout')),
                                     method='GET',
                                     verify=Setting().get('verify_ssl_connections'))
            return jdata
        except Exception as e:
            current_app.logger.error(
                "Can not get server statistics. DETAIL: {0}".format(e))
            current_app.logger.debug(traceback.format_exc())
            return []

    def global_search(self, object_type='all', query=''):
        """
        Search zone/record/comment directly from PDNS API
        """
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY

        try:
            jdata = utils.fetch_json(urljoin(
                self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                '/servers/{}/search-data?object_type={}&q={}'.format(
                    self.server_id, object_type, query)),
                                     headers=headers,
                                     timeout=int(
                                         Setting().get('pdns_api_timeout')),
                                     method='GET',
                                     verify=Setting().get('verify_ssl_connections'))
            return jdata
        except Exception as e:
            current_app.logger.error(
                "Can not make global search. DETAIL: {0}".format(e))
            current_app.logger.debug(traceback.format_exc())
            return []
