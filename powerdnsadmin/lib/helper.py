import requests
from urllib.parse import unquote, urljoin
from flask import abort, current_app, g, request

from ..models import Setting
from .errors import DomainAccessForbidden


class UpstreamPathRejected(Exception):
    """The request path contains a segment that would change the upstream target."""


def _is_dot_segment(segment):
    """True when this path segment is ``.`` or ``..``, including percent-encoding."""
    current = segment
    for _ in range(3):
        if current in ('.', '..'):
            return True
        decoded = unquote(current)
        if decoded == current:
            return False
        current = decoded
    return current in ('.', '..')


def canonical_request_path():
    """Return the request path that may be forwarded to PowerDNS.

    ``urljoin`` removes ``..`` segments. A scoped key authorized for
    ``allowed-zone`` could otherwise be forwarded to ``private-zone``
    together with the backend API key. Dot segments are rejected instead
    of being resolved.
    """
    candidates = [request.path or '']
    raw = request.environ.get('RAW_URI') or request.environ.get('REQUEST_URI') or ''
    if raw:
        candidates.append(raw.split('?', 1)[0])
    for candidate in candidates:
        for segment in candidate.split('/'):
            if segment and _is_dot_segment(segment):
                raise UpstreamPathRejected()
    return request.path or '/'


def zone_from_path(path):
    """Return the zone named in a PowerDNS API path, without a trailing dot."""
    parts = [part for part in (path or '').split('/') if part]
    try:
        index = parts.index('zones')
    except ValueError:
        return None
    if index + 1 >= len(parts):
        return None
    zone_name = unquote(parts[index + 1]).rstrip('.')
    if not zone_name or _is_dot_segment(zone_name):
        raise UpstreamPathRejected()
    return zone_name


def apikey_can_reach_zone(zone_name):
    """Whether the current API key may act on this canonical zone name."""
    if zone_name is None:
        return True
    apikey = getattr(g, 'apikey', None)
    if apikey is None:
        return True
    role = getattr(getattr(apikey, 'role', None), 'name', None)
    if role in ('Administrator', 'Operator'):
        return True
    names = {item.name for item in (getattr(apikey, 'domains', None) or ())}
    for account in getattr(apikey, 'accounts', None) or ():
        names.update(domain.name for domain in account.domains)
    return zone_name in names


def upstream_request_url(base_url):
    """Build the PowerDNS URL for this request, or reject a traversal path."""
    path = canonical_request_path()
    zone_name = zone_from_path(path)
    if not apikey_can_reach_zone(zone_name):
        raise DomainAccessForbidden()
    target = path
    if request.query_string:
        target += '?' + request.query_string.decode('latin-1')
    return urljoin(base_url, target)


def forward_request():
    pdns_api_url = Setting().get('pdns_api_url')
    pdns_api_key = Setting().get('pdns_api_key')
    headers = {}
    data = None

    msg_str = "Sending request to powerdns API {0}"

    if request.method != 'GET' and request.method != 'DELETE':
        msg = msg_str.format(request.get_json(force=True, silent=True))
        current_app.logger.debug(msg)
        data = request.get_json(force=True, silent=True)

    try:
        url = upstream_request_url(pdns_api_url)
    except UpstreamPathRejected:
        current_app.logger.warning(
            'Rejected PowerDNS proxy path with a traversal segment')
        abort(400)

    verify = Setting().get('verify_ssl_connections')

    headers = {
        'user-agent': 'powerdns-admin/api',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'accept': 'application/json; q=1',
        'X-API-KEY': pdns_api_key
    }

    resp = requests.request(request.method,
                            url,
                            headers=headers,
                            verify=verify,
                            json=data)

    return resp
