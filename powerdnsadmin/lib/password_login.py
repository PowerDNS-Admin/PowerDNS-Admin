"""Rules shared by the login form, browser Basic auth, and API Basic auth.

API keys are a separate credential and do not pass through here. A user
password presented anywhere else has to satisfy the same account policy as
the login form. When the account has a TOTP secret, the one-time code is
read from the ``X-OTP`` header because Basic authentication has no second
field of its own.
"""
from datetime import datetime, timedelta

from sqlalchemy.exc import OperationalError

from .auth_throttle import THROTTLE_MESSAGE


# The browser challenge, API Basic authentication, and DynDNS share this
# account-level budget. Five wrong codes lock the account. Each new lock,
# after the previous one has expired, lasts longer: 5, 15, 30, 60, and 120
# minutes, then 4 hours, 8 hours, and double that until a week.
OTP_FAILURE_LIMIT = 5
_OTP_LOCK_MINUTES = (5, 15, 30, 60, 120, 240, 480)
_OTP_LOCK_MAX_MINUTES = 7 * 24 * 60
OTP_FAILURE_MESSAGE = 'Too many authentication attempts. Please sign in again.'
OTP_CONFIRMATION_MESSAGE = (
    'Enter the current authentication code to change two-factor authentication.'
)


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


# Compare-and-swap retries. SQLite does not honor SELECT … FOR UPDATE, so two
# requests can read the same counter. The update itself matches the value that
# was read and is retried when another request won the race.
_OTP_UPDATE_RETRIES = 10


def _database_user_id(user):
    """Account id when this process has a database, else ``None``.

    Unit tests authenticate a mock account that has no integer id. Those
    requests must not reach the lock counter.
    """
    from flask import current_app

    if 'sqlalchemy' not in current_app.extensions:
        return None
    user_id = getattr(user, 'id', None)
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        return None
    return user_id


def _retryable_database_error(exc):
    message = str(getattr(exc, 'orig', exc)).lower()
    return (
        'database is locked' in message
        or 'database table is locked' in message
        or 'deadlock' in message
        or 'try restarting transaction' in message
    )


def _otp_models():
    from ..models.base import db
    from ..models.user import User
    return db, User


def otp_lock_minutes(lock_number):
    """Minutes for lock number 1, 2, 3, and so on."""
    number = max(int(lock_number or 1), 1)
    if number <= len(_OTP_LOCK_MINUTES):
        minutes = _OTP_LOCK_MINUTES[number - 1]
    else:
        extra = number - len(_OTP_LOCK_MINUTES)
        if extra > 16:
            return _OTP_LOCK_MAX_MINUTES
        minutes = _OTP_LOCK_MINUTES[-1] * (2 ** extra)
    if minutes > _OTP_LOCK_MAX_MINUTES:
        return _OTP_LOCK_MAX_MINUTES
    return minutes


def format_unlock_time(locked_until):
    """Clock time shown for an automatic unlock. The value is UTC."""
    return locked_until.strftime('%Y-%m-%d %H:%M UTC')


def otp_lock_message(_locked_until=None):
    """User-facing reason. The unlock time stays in the audit log."""
    return THROTTLE_MESSAGE


def _clear_expired_otp_lock(user_id, now):
    """Drop an elapsed lock in one statement so a stale read cannot restore it."""
    db, User = _otp_models()
    db.session.query(User).filter(
        User.id == user_id,
        User.otp_locked_until.isnot(None),
        User.otp_locked_until <= now,
    ).update(
        {
            User.otp_failed_attempts: 0,
            User.otp_locked_until: None,
        },
        synchronize_session=False,
    )


def _load_otp_row(user_id):
    db, User = _otp_models()
    db.session.expire_all()
    return db.session.query(User).filter(User.id == user_id).one_or_none()


def otp_failure_state(user):
    """Current counter and unlock time, or ``None`` when there is no database row."""
    user_id = _database_user_id(user)
    if user_id is None:
        return None
    db, _User = _otp_models()
    now = datetime.utcnow()
    _clear_expired_otp_lock(user_id, now)
    db.session.commit()
    row = _load_otp_row(user_id)
    if row is None:
        return None
    locked_until = None
    if row.otp_locked_until is not None and row.otp_locked_until > now:
        locked_until = row.otp_locked_until
    return {
        'attempts': row.otp_failed_attempts or 0,
        'limit': OTP_FAILURE_LIMIT,
        'locked_until': locked_until,
        'lockouts': row.otp_lockouts or 0,
    }


def otp_failures_blocked(user):
    """Return a reason when this account has used its authentication attempts."""
    state = otp_failure_state(user)
    if state and state['locked_until']:
        return otp_lock_message(state['locked_until'])
    return None


def _claim_otp_failure(user_id):
    """Apply one failure if the row still has the values just read.

    ``False`` means another request wrote the row first and the caller retries.
    """
    db, User = _otp_models()
    now = datetime.utcnow()
    _clear_expired_otp_lock(user_id, now)
    row = _load_otp_row(user_id)
    if row is None:
        db.session.rollback()
        return None

    unlocked = db.or_(
        User.otp_locked_until.is_(None),
        User.otp_locked_until <= now,
    )
    if row.otp_locked_until is not None and row.otp_locked_until > now:
        locked_until = row.otp_locked_until
        lockouts = row.otp_lockouts or 0
        if (row.otp_failed_attempts or 0) != OTP_FAILURE_LIMIT:
            claimed = db.session.query(User).filter(
                User.id == user_id,
                User.otp_locked_until == locked_until,
            ).update(
                {User.otp_failed_attempts: OTP_FAILURE_LIMIT},
                synchronize_session=False,
            )
            if claimed != 1:
                db.session.rollback()
                return False
        db.session.commit()
        return {
            'attempts': OTP_FAILURE_LIMIT,
            'limit': OTP_FAILURE_LIMIT,
            'locked_until': locked_until,
            'lock_minutes': None,
            'lockouts': lockouts,
        }

    expected = row.otp_failed_attempts or 0
    lockouts = row.otp_lockouts or 0
    if expected + 1 >= OTP_FAILURE_LIMIT:
        minutes = otp_lock_minutes(lockouts + 1)
        locked_until = now + timedelta(minutes=minutes)
        claimed = db.session.query(User).filter(
            User.id == user_id,
            User.otp_failed_attempts == expected,
            User.otp_lockouts == lockouts,
            unlocked,
        ).update(
            {
                User.otp_failed_attempts: OTP_FAILURE_LIMIT,
                User.otp_lockouts: lockouts + 1,
                User.otp_locked_until: locked_until,
            },
            synchronize_session=False,
        )
        if claimed != 1:
            db.session.rollback()
            return False
        db.session.commit()
        return {
            'attempts': OTP_FAILURE_LIMIT,
            'limit': OTP_FAILURE_LIMIT,
            'locked_until': locked_until,
            'lock_minutes': minutes,
            'lockouts': lockouts + 1,
        }

    claimed = db.session.query(User).filter(
        User.id == user_id,
        User.otp_failed_attempts == expected,
        unlocked,
    ).update(
        {User.otp_failed_attempts: expected + 1},
        synchronize_session=False,
    )
    if claimed != 1:
        db.session.rollback()
        return False
    db.session.commit()
    return {
        'attempts': expected + 1,
        'limit': OTP_FAILURE_LIMIT,
        'locked_until': None,
        'lock_minutes': None,
        'lockouts': lockouts,
    }


def register_otp_failure(user):
    """Count one rejected authentication code against the shared account limit.

    The returned state is the counter after this failure. Hitting the limit
    starts the next staggered lock and leaves the counter at that limit.
    Concurrent callers cannot publish the same count: the write matches the
    count that was read, which SQLite and MySQL both apply atomically.
    """
    user_id = _database_user_id(user)
    if user_id is None:
        return None
    db, _User = _otp_models()
    for _attempt in range(_OTP_UPDATE_RETRIES):
        try:
            state = _claim_otp_failure(user_id)
        except OperationalError as exc:
            db.session.rollback()
            if not _retryable_database_error(exc):
                raise
            continue
        if state is not False:
            return state
    raise RuntimeError('Could not record the authentication failure')


def clear_otp_failures(user):
    """Forget rejected codes after one is accepted."""
    user_id = _database_user_id(user)
    if user_id is None:
        return
    db, User = _otp_models()
    db.session.query(User).filter(User.id == user_id).update(
        {
            User.otp_failed_attempts: 0,
            User.otp_locked_until: None,
            User.otp_lockouts: 0,
        },
        synchronize_session=False,
    )
    db.session.commit()


def otp_enrollment_required(user):
    """Forced MFA applies to every password login, not only the browser form."""
    if getattr(user, 'otp_secret', None):
        return False
    from ..models.setting import Setting
    setting = Setting()
    return bool(setting.get('otp_force') and setting.get('otp_field_enabled'))


def otp_confirmation_blocked(user, otp_token):
    """Return an error when a signed-in change lacks a current code.

    Profile changes and an administrator removing their own MFA use the same
    lock as sign-in, so a stolen session cannot guess codes without limit.
    """
    blocked = otp_failures_blocked(user)
    if blocked:
        return blocked
    token = '' if otp_token is None else str(otp_token).strip()
    if not token.isdigit() or not user.verify_totp(token):
        register_otp_failure(user)
        return otp_failures_blocked(user) or OTP_CONFIRMATION_MESSAGE
    clear_otp_failures(user)
    return None


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
