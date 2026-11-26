"""Retrieve BIND-compatible zone files from PowerDNS."""

from urllib.parse import quote, urljoin

from flask import Response, abort, current_app
from requests.exceptions import RequestException

from ..models.setting import Setting
from . import utils


def export_allowed(role):
    return role in {'Administrator', 'Operator'} or (
        role == 'User' and Setting().get('allow_user_export_domain'))


def export_zone(zone_name, server_id='localhost'):
    settings = Setting()
    path = (
        f'{utils.pdns_api_extended_uri()}/servers/{quote(server_id, safe="")}'
        f'/zones/{quote(zone_name.rstrip(".") + ".", safe="")}/export'
    )
    try:
        result = utils.fetch_json(
            urljoin(settings.get('pdns_api_url'), path),
            headers={'X-API-Key': settings.get('pdns_api_key')},
            timeout=int(settings.get('pdns_api_timeout')),
            verify=settings.get('verify_ssl_connections'))
    except (RequestException, RuntimeError, ValueError):
        current_app.logger.exception('Cannot export zone %s', zone_name)
        abort(502, description='Cannot export the zone from PowerDNS.')
    if not isinstance(result, dict) or not isinstance(result.get('zone'), str):
        abort(502, description='PowerDNS returned an invalid zone export.')
    return result['zone']


def zone_download(zone_name, content):
    filename = quote(zone_name.rstrip('.'), safe='.-') + '.zone'
    response = Response(content.encode("utf-8"), mimetype="text/plain")
    response.headers.set("Content-Disposition", "attachment", filename=filename)
    response.headers['Cache-Control'] = 'no-store'
    return response
