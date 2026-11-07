import base64
import binascii
import json
from datetime import datetime
from urllib.parse import parse_qsl, urlencode

from flask import current_app, g, request
from sqlalchemy.orm import Session

from ..models.api_history import ApiHistory
from ..models.base import db
from .client_request import request_host_and_user_agent

_REDACTED = '[redacted]'
_MAX_PATH_LENGTH = 512
_MAX_QUERY_STRING_LENGTH = 4096
_MAX_BODY_LENGTH = 32768
_REQUEST_BODY_OMITTED = '{"_omitted":"request body exceeded audit size limit"}'
_RESPONSE_BODY_OMITTED = '{"_omitted":"response body exceeded audit size limit"}'
_SENSITIVE_KEY_NAMES = frozenset({
    'password',
    'plain_text_password',
    'plaintext_password',
    'plain_key',
    'otp',
    'otp_secret',
    'secret',
    'token',
    'access_token',
    'refresh_token',
    'authorization',
    'api_key',
    'apikey',
    'x_api_key',
})
_SENSITIVE_KEY_PARTS = ('password', 'secret', 'token', 'apikey', 'api_key')


def is_sensitive_key(key):
    normalized = str(key).lower().replace('-', '_')
    if normalized in _SENSITIVE_KEY_NAMES:
        return True
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def redact_for_audit(value):
    """Return a copy of value with credential fields replaced."""
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            if is_sensitive_key(key):
                redacted[key] = _REDACTED
            else:
                redacted[key] = redact_for_audit(item)
        return redacted
    if isinstance(value, list):
        return [redact_for_audit(item) for item in value]
    return value


def should_audit_path(path):
    """Every request the app serves under /api, including the PowerDNS proxy."""
    return path == '/api' or path.startswith('/api/')


def _encode_audit_body(payload, omitted):
    encoded = json.dumps(
        redact_for_audit(payload),
        default=str,
        separators=(',', ':'),
    )
    if len(encoded) > _MAX_BODY_LENGTH:
        return omitted
    return encoded


def serialize_request_body(payload):
    if payload is None:
        return None
    return _encode_audit_body(payload, _REQUEST_BODY_OMITTED)


def serialize_response_text(raw):
    """Store the API response text, with credential fields removed.

    Bodies larger than the audit limit are replaced with a marker. The
    original text is not kept, so a secret inside an oversized payload is
    not written to the history row.
    """
    if raw is None:
        return None
    text = str(raw).replace('\x00', '')
    if not text:
        return None
    if len(text) > _MAX_BODY_LENGTH:
        return _RESPONSE_BODY_OMITTED
    try:
        payload = json.loads(text)
    except (TypeError, ValueError):
        return text
    return _encode_audit_body(payload, _RESPONSE_BODY_OMITTED)


def redact_query_string(raw):
    if not raw:
        return None
    cleaned = []
    for key, value in parse_qsl(raw, keep_blank_values=True):
        if is_sensitive_key(key):
            cleaned.append((key, _REDACTED))
        else:
            cleaned.append((key, value))
    if not cleaned:
        return None
    return urlencode(cleaned)[:_MAX_QUERY_STRING_LENGTH]


def _integer_id(value):
    """Keep only a real database id.

    Unit tests authenticate with mock users whose id is not an integer.
    Writing that value makes the audit insert fail and drops the row.
    """
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def _clip(value, limit):
    if value is None:
        return None
    text = str(value).replace('\x00', '')
    if not text:
        return None
    return text[:limit]


def _attempted_basic_username():
    header = request.headers.get('Authorization', '')
    if not header.startswith('Basic '):
        return None
    try:
        decoded = base64.b64decode(header[6:], validate=True)
        text = decoded.decode('utf-8')
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return None
    username, separator, _password = text.partition(':')
    if not separator:
        return None
    return _clip(username.strip(), 128)


def _actor():
    user = getattr(g, 'basic_auth_user', None)
    apikey = getattr(g, 'apikey', None)
    actor = {
        'auth_type': 'none',
        'authenticated': False,
        'user_id': None,
        'username': None,
        'apikey_id': None,
        'apikey_description': None,
    }
    if apikey is not None and getattr(apikey, 'id', None):
        actor.update({
            'auth_type': 'api_key',
            'authenticated': True,
            'apikey_id': _integer_id(apikey.id),
            'apikey_description': _clip(
                getattr(apikey, 'description', None), 255),
        })
        return actor
    if user is not None and getattr(user, 'id', None):
        actor.update({
            'auth_type': 'basic',
            'authenticated': True,
            'user_id': _integer_id(user.id),
            'username': _clip(getattr(user, 'username', None), 128),
        })
        return actor
    if request.headers.get('X-API-KEY'):
        actor['auth_type'] = 'api_key'
        return actor
    if request.headers.get('Authorization'):
        actor['auth_type'] = 'basic'
        actor['username'] = _attempted_basic_username()
    return actor


def _request_body():
    payload = request.get_json(silent=True)
    return serialize_request_body(payload)


def _response_body(response):
    status_code = getattr(response, 'status_code', None)
    if status_code in (204, 304):
        return None
    getter = getattr(response, 'get_data', None)
    if getter is None:
        return None
    try:
        # as_text decodes with the response charset. Binary bodies are skipped.
        text = getter(as_text=True)
    except (RuntimeError, UnicodeDecodeError):
        return None
    return serialize_response_text(text)


def _insert(row):
    audit_session = Session(bind=db.engine)
    try:
        audit_session.add(row)
        audit_session.commit()
    except Exception:
        audit_session.rollback()
        raise
    finally:
        audit_session.close()


def record_api_request(response):
    """Write one api_history row for this /api request.

    Failures here must not change the response the caller already received.
    """
    try:
        path = request.path or ''
        if not should_audit_path(path):
            return
        actor = _actor()
        remote_addr = _clip(request.remote_addr, 255)
        host, user_agent = request_host_and_user_agent()
        query_string = redact_query_string(
            request.query_string.decode('utf-8', errors='replace'))
        row = ApiHistory(
            created_on=datetime.utcnow(),
            method=_clip(request.method, 16) or 'GET',
            path=_clip(path, _MAX_PATH_LENGTH) or '/api',
            query_string=query_string,
            status_code=getattr(response, 'status_code', None),
            remote_addr=remote_addr,
            host=host,
            user_agent=user_agent,
            auth_type=actor['auth_type'],
            authenticated=actor['authenticated'],
            user_id=actor['user_id'],
            username=actor['username'],
            apikey_id=actor['apikey_id'],
            apikey_description=actor['apikey_description'],
            request_body=_request_body(),
            response_body=_response_body(response),
        )
        _insert(row)
    except Exception:
        try:
            current_app.logger.exception('Failed to record API history')
        except Exception:
            pass
