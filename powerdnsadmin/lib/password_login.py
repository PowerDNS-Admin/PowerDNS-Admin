"""Rules shared by the login form, browser Basic auth, and API Basic auth.

API keys are a separate credential and do not pass through here. A user
password presented anywhere else has to satisfy the same account policy as
the login form. When the account has a TOTP secret, the one-time code is
read from the ``X-OTP`` header because Basic authentication has no second
field of its own.
"""
from datetime import datetime, timedelta


# The browser challenge, API Basic authentication, and DynDNS share this
# account-level budget. Five wrong codes lock the account for five minutes.
OTP_FAILURE_LIMIT = 5
OTP_FAILURE_LOCK_SECONDS = 300
OTP_FAILURE_MESSAGE = 'Too many authentication attempts. Please sign in again.'


def password_login_blocked(user, method, local_db_enabled, verify_user_email):
    """Return a user-facing reason to stop, or ``None`` when the password may be checked.

    ``local_db_enabled`` is only treated as off when it is explicitly false.
    A missing setting keeps the historical default, which is local login on.
    """
    if method == 'LOCAL' and local_db_enabled is False:
        return 'Local authentication is disabled'
    if (verify_user_email and getattr(user, 'email', None)
            and not user.confirmed):
        return 'Please confirm your email address first'
    return None


def _persistent_user(user):
    """The database row for an account, when this process has a database."""
    from flask import current_app

    if 'sqlalchemy' not in current_app.extensions:
        return None
    user_id = getattr(user, 'id', None)
    if not user_id:
        return None
    from ..models.base import db
    from ..models.user import User
    return db.session.get(User, user_id)


def _clear_expired_otp_lock(row):
    if row.otp_locked_until is None or row.otp_locked_until > datetime.utcnow():
        return False
    row.otp_failed_attempts = 0
    row.otp_locked_until = None
    return True


def otp_failures_blocked(user):
    """Return a reason when this account has used its authentication attempts."""
    from ..models.base import db

    row = _persistent_user(user)
    if row is None:
        return None
    if _clear_expired_otp_lock(row):
        db.session.commit()
    if row.otp_locked_until is not None and row.otp_locked_until > datetime.utcnow():
        return OTP_FAILURE_MESSAGE
    return None


def register_otp_failure(user):
    """Count one rejected authentication code against the shared account limit."""
    from ..models.base import db

    row = _persistent_user(user)
    if row is None:
        return
    _clear_expired_otp_lock(row)
    row.otp_failed_attempts = (row.otp_failed_attempts or 0) + 1
    if row.otp_failed_attempts >= OTP_FAILURE_LIMIT:
        row.otp_locked_until = datetime.utcnow() + timedelta(
            seconds=OTP_FAILURE_LOCK_SECONDS)
    db.session.commit()


def clear_otp_failures(user):
    """Forget rejected codes after one is accepted."""
    from ..models.base import db

    row = _persistent_user(user)
    if row is None:
        return
    if not row.otp_failed_attempts and row.otp_locked_until is None:
        return
    row.otp_failed_attempts = 0
    row.otp_locked_until = None
    db.session.commit()


def otp_enrollment_required(user):
    """Forced MFA applies to every password login, not only the browser form."""
    if getattr(user, 'otp_secret', None):
        return False
    from ..models.setting import Setting
    setting = Setting()
    return bool(setting.get('otp_force') and setting.get('otp_field_enabled'))


def otp_login_blocked(user, otp_token):
    """Return a reason when this account requires a one-time code that was not accepted."""
    if not getattr(user, 'otp_secret', None):
        if otp_enrollment_required(user):
            return 'Multi-factor authentication enrollment is required'
        return None
    blocked = otp_failures_blocked(user)
    if blocked:
        return blocked
    token = '' if otp_token is None else str(otp_token).strip()
    if not token.isdigit() or not user.verify_totp(token):
        register_otp_failure(user)
        return 'Multi-factor authentication required'
    clear_otp_failures(user)
    return None
