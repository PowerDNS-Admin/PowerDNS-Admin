"""Record application setting changes for the System Activity page."""

from flask import g, has_request_context, request

from ..models.base import db
from ..models.system_history import SystemHistory

_REDACTED = '[redacted]'
_MAX_VALUE_LENGTH = 4000
_SECRET_NAMES = frozenset({
    'secret_key',
    'salt',
    'saml_key',
    'github_oauth_key',
    'azure_oauth_key',
    'oidc_oauth_key',
})


def setting_value_is_secret(name):
    """True when the stored value is a password, key, or other credential."""
    normalized = str(name or '').lower()
    if normalized in _SECRET_NAMES:
        return True
    return normalized.endswith(('_password', '_secret', '_api_key'))


def display_setting_value(name, value):
    """Return the text to store. Credentials are replaced, other values clipped."""
    if value is None:
        return None
    text = str(value).replace('\x00', '')
    if text == '':
        return ''
    if setting_value_is_secret(name):
        return _REDACTED
    return text[:_MAX_VALUE_LENGTH]


def _actor():
    username = None
    user_id = None
    remote_addr = None
    if not has_request_context():
        return username, user_id, remote_addr
    remote_addr = request.remote_addr
    user = getattr(g, 'basic_auth_user', None)
    if user is None:
        try:
            from flask_login import current_user
            if current_user is not None and getattr(
                    current_user, 'is_authenticated', False):
                user = current_user
        except Exception:
            user = None
    if user is not None and getattr(user, 'id', None):
        username = getattr(user, 'username', None)
        user_id = user.id
    if remote_addr:
        remote_addr = str(remote_addr)[:255]
    if username:
        username = str(username).replace('\x00', '')[:128]
    return username, user_id, remote_addr


def queue_setting_change(setting_name, old_value, new_value):
    """Add a system-activity row to the current database session.

    The caller commits. An unchanged value is not recorded. This does not
    commit and does not query the setting table.
    """
    old_text = None if old_value is None else str(old_value)
    new_text = None if new_value is None else str(new_value)
    if old_text == new_text:
        return
    username, user_id, remote_addr = _actor()
    db.session.add(SystemHistory(
        setting_name=str(setting_name)[:64],
        old_value=display_setting_value(setting_name, old_text),
        new_value=display_setting_value(setting_name, new_text),
        username=username,
        user_id=user_id,
        remote_addr=remote_addr,
    ))
