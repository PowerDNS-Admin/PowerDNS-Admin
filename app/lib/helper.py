from app.models import Setting
import requests
from flask import request
import logging as logger
from urllib.parse import urljoin

logging = logger.getLogger(__name__)


def forward_request():
    pdns_api_url = Setting().get('pdns_api_url')
    pdns_api_key = Setting().get('pdns_api_key')
    headers = {}
    data = None

    msg_str = "Sending request to powerdns API {0}"

    if request.method != 'GET' and request.method != 'DELETE':
        msg = msg_str.format(request.get_json(force=True))
        logging.debug(msg)
        data = request.get_json(force=True)

    verify = False

    headers = {
        'user-agent': 'powerdnsadmin/0',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'accept': 'application/json; q=1',
        'X-API-KEY': pdns_api_key
    }

    url = urljoin(pdns_api_url, request.path)

    resp = requests.request(
        request.method,
        url,
        headers=headers,
        verify=verify,
        json=data
    )

    return resp
