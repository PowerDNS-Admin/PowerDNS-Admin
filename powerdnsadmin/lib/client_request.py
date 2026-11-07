"""Host and user agent taken from the current request for audit rows."""

from flask import has_request_context, request

_MAX_HOST_LENGTH = 255
_MAX_USER_AGENT_LENGTH = 512


def _clip(value, limit):
    if value is None:
        return None
    text = str(value).replace('\x00', '').strip()
    if not text:
        return None
    return text[:limit]


def request_host_and_user_agent():
    """Return the Host header and User-Agent, or ``(None, None)`` outside a request."""
    if not has_request_context():
        return None, None
    return (
        _clip(request.host, _MAX_HOST_LENGTH),
        _clip(request.headers.get('User-Agent'), _MAX_USER_AGENT_LENGTH),
    )
