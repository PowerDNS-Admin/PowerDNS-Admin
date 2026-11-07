"""Shared limits checked before a password hash or an LDAP bind.

The budgets are independent of the one-time-code lock. A wrong password
never starts that week-long lock, and a correct password does not erase
failures this source already collected against other accounts.

Counters live in the database so workers and instances share one budget.
"""
import contextvars
import ipaddress
import json
import time
import uuid
from datetime import datetime, timedelta

from flask import current_app, has_request_context, request
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError


THROTTLE_MESSAGE = 'Too many authentication attempts. Try again later.'

_SOURCE_LIMIT = 20
_ACCOUNT_LIMIT = 10
_PAIR_LIMIT = 5
_SOURCE_WINDOW = 300
_ACCOUNT_WINDOW = 900
_PAIR_WINDOW = 900
_COOLDOWNS = (30, 60, 300, 900, 1800)
_MAX_IN_FLIGHT = 32
_IN_FLIGHT_LEASE = 30
_SPRAY_USERNAMES = 10
_SPRAY_SOURCES = 5
_SUCCESS_AFTER = 3
_SEEN_CAP = 32
_USERNAME_LIMIT = 64
_PASSWORD_LIMIT = 256
_HEADER_LIMIT = 1024
_RETRIES = 8
_PRUNE_AFTER = timedelta(hours=2)

_SCOPE_INFLIGHT = 'inflight'
_SCOPE_APIKEY = 'apikey'
_MISSING = object()
_logged_missing_table = False
_auth_deadline = contextvars.ContextVar('auth_deadline', default=None)


class AuthenticationThrottled(Exception):
    """A password attempt was refused before the expensive check."""

    def __init__(self, retry_after):
        self.retry_after = max(1, int(retry_after))
        super().__init__(THROTTLE_MESSAGE)


class ThrottleStoreUnavailable(Exception):
    """The shared limiter table is missing, so production must not authenticate."""


class PasswordAttempt:
    """Hold one shared concurrency slot around a password check."""

    def __init__(self, username, password, trust_user, source):
        self.username = username
        self.password = password
        self.trust_user = trust_user
        self.source = source
        self.skip = False
        self.lease = None
        self._deadline_token = None

    def __enter__(self):
        if self.trust_user:
            return self
        if not credentials_bounded(self.username, self.password):
            self.skip = True
            retry = record_malformed(self.source)
            if retry:
                raise AuthenticationThrottled(retry)
            return self
        retry = active_retry_after(self.source, self.username)
        if retry:
            raise AuthenticationThrottled(retry)
        held = acquire_inflight()
        if held is None:
            # Tests authenticate without the migrated table. A deployed
            # process must not keep checking passwords with no shared limit.
            if not current_app.config.get('TESTING'):
                raise ThrottleStoreUnavailable()
            self._start_deadline(None)
            return self
        if not held:
            raise AuthenticationThrottled(1)
        token, expires = held
        self.lease = token
        self._start_deadline(expires)
        return self

    def _start_deadline(self, expires):
        """Stop directory calls when this check's lease ends.

        ``expires`` is the timestamp written on the slot. Time spent claiming
        that slot is already gone, so LDAP does not receive a new full lease.
        """
        if expires is None:
            remaining = float(inflight_lease_seconds())
        else:
            remaining = (expires - datetime.utcnow()).total_seconds()
            if remaining < 0:
                remaining = 0
        self._deadline_token = _auth_deadline.set(
            time.monotonic() + remaining)

    def __exit__(self, exc_type, exc, tb):
        try:
            if self.lease:
                release_inflight(self.lease)
                self.lease = None
        finally:
            if self._deadline_token is not None:
                _auth_deadline.reset(self._deadline_token)
                self._deadline_token = None
        return False


def credentials_bounded(username, password):
    """False when the credential is too large to hash or look up."""
    if _bounded_text(username, _USERNAME_LIMIT) is None:
        return False
    if password is None:
        return True
    return _bounded_text(password, _PASSWORD_LIMIT) is not None


def normalize_username(username):
    text = _bounded_text(username, _USERNAME_LIMIT)
    if text is None:
        return None
    folded = text.casefold()
    if not folded:
        return None
    return folded


def authentication_source(fallback=''):
    """Client address for a throttle key.

    X-Forwarded-For is used only after the connection peer is a configured
    trusted proxy. A caller-supplied header cannot choose a fresh budget.
    """
    if not has_request_context():
        parsed = _parse_ip(fallback)
        return str(parsed) if parsed is not None else 'unknown'
    peer = _direct_peer()
    if peer is None:
        return 'unknown'
    trusted = _trusted_networks()
    if not trusted or not _in_networks(peer, trusted):
        return str(peer)
    for address in reversed(_forwarded_addresses()):
        if not _in_networks(address, trusted):
            return str(address)
    return str(peer)


def active_retry_after(source, username):
    """Seconds until every applicable budget is open, or ``None``."""
    waits = []
    now = _now()
    for scope, subject in _keys(source, normalize_username(username)):
        row = _load(scope, subject)
        if (row is None or row is _MISSING or row.locked_until is None
                or row.locked_until <= now):
            continue
        waits.append(_seconds_until(row.locked_until, now))
    if not waits:
        return None
    return max(waits)


def record_malformed(source):
    """Count an unusable credential against the source budget only."""
    return _record(source, None, malformed=True)


def note_wrong_password(username, source):
    """Spend source, account, and pair budgets. Raise when one is now closed."""
    retry = _record(source, normalize_username(username), malformed=False)
    if retry:
        raise AuthenticationThrottled(retry)


def note_correct_password(username, source):
    """Clear this account's budget and leave the source's other failures."""
    username = normalize_username(username)
    if not username:
        return
    pair_failures = _failures('pair', _pair_subject(source, username))
    account_failures = _failures('account', username)
    observed = max(pair_failures, account_failures)
    _clear('account', username)
    _clear('pair', _pair_subject(source, username))
    if observed >= _setting('AUTH_SUCCESS_AFTER_FAILURES', _SUCCESS_AFTER):
        current_app.logger.warning(
            'Authentication succeeded for %s from %s after %s failed attempts',
            username, source, observed)


def record_password_failure(source, username):
    """Test and worker entry point for one shared failed guess."""
    _record(source, normalize_username(username), malformed=False)


def api_key_bounded(token):
    """False when the key must not be hashed.

    The limit matches a password. The token itself is not a counter key.
    """
    return _bounded_text(token, _PASSWORD_LIMIT) not in (None, '')


def api_key_retry_after(source):
    """Seconds until this source may present another API key, or ``None``.

    This budget is only the source address. It does not read or spend the
    password or one-time-code counters.
    """
    if not _api_key_limiter_active():
        return None
    row = _load(_SCOPE_APIKEY, source)
    now = _now()
    if (row is None or row is _MISSING or row.locked_until is None
            or row.locked_until <= now):
        return None
    return _seconds_until(row.locked_until, now)


def note_rejected_api_key(source):
    """Count one unusable API key for this source. Return seconds when it closes.

    Invalid, malformed, and oversized keys share the counter. The token is
    not stored or written to the log.
    """
    if not _api_key_limiter_active():
        return None
    return _bump(
        _SCOPE_APIKEY, source,
        _setting('AUTH_SOURCE_LIMIT', _SOURCE_LIMIT),
        _setting('AUTH_SOURCE_WINDOW', _SOURCE_WINDOW),
        None, source, None)


def claim_api_key_slot():
    """Take one shared CPU slot before hashing an API key.

    ``None`` means this process is not limiting keys. ``False`` means every
    slot is already held. A token is the slot this call must release.
    """
    if not _api_key_limiter_active():
        return None
    held = acquire_inflight()
    if held is None:
        if current_app.config.get('TESTING'):
            return None
        raise ThrottleStoreUnavailable()
    if not held:
        return False
    return held[0]


def _api_key_limiter_active():
    """True when API-key failures can be recorded.

    Tests without the application database keep working. A deployed process
    with no throttle table must not hash keys without a limit.
    """
    if 'sqlalchemy' not in current_app.extensions:
        ready = False
    else:
        ready = throttle_store_ready()
    if ready:
        return True
    if current_app.config.get('TESTING'):
        return False
    raise ThrottleStoreUnavailable()


def inflight_lease_seconds():
    """How long one password check may hold a concurrency slot."""
    return _setting('AUTH_IN_FLIGHT_LEASE', _IN_FLIGHT_LEASE)


def remaining_authentication_seconds():
    """Seconds left on this check's deadline, or ``None`` outside a check.

    The deadline is the concurrency lease. Directory calls share it, so a
    search cannot restart the full timeout before the bind.
    """
    deadline = _auth_deadline.get()
    if deadline is None:
        return None
    return deadline - time.monotonic()


def throttle_store_ready():
    """False when the shared authentication table cannot be read."""
    db, AuthAttempt = _models()

    def op():
        db.session.query(AuthAttempt.id).limit(1).all()
        return True

    try:
        return bool(_run(op))
    except _StoreUnavailable:
        return False


def assert_throttle_store():
    """Stop startup when a missed migration would disable the limiter."""
    if throttle_store_ready():
        return
    raise RuntimeError(
        'Refusing to start because the auth_attempt table is missing. '
        'Run flask db upgrade before serving authentication.'
    )


def acquire_inflight():
    """Take one password-check slot owned by this call.

    The return value is ``(token, expires)``. ``expires`` is the timestamp
    stored on the slot, and the authentication deadline is derived from it.
    ``None`` means the shared table is absent. ``False`` means every
    unexpired slot is already held.

    Slots are the fixed subjects ``0`` .. ``limit-1``. The unique
    ``(scope, subject)`` index admits at most one owner per slot. An expired
    slot is reclaimed by a conditional update, and a free slot by an insert.
    Losing either claim tries the next slot. A later read of inserted ids is
    not used, because an autoincrement value and the commit order can differ.
    """
    limit = _setting('AUTH_MAX_IN_FLIGHT', _MAX_IN_FLIGHT)
    now = _now()
    if _expire_inflight(now) is _MISSING:
        return None
    expires = now + timedelta(seconds=inflight_lease_seconds())
    for slot in range(limit):
        token = uuid.uuid4().hex
        claimed = _claim_slot(str(slot), token, now, expires)
        if claimed is None:
            return None
        if claimed:
            return token, expires
    return False


def release_inflight(token):
    """Drop the slot acquired by this check. Other slots stay held."""
    if not token:
        return
    db, AuthAttempt = _models()

    def op():
        db.session.query(AuthAttempt).filter(
            AuthAttempt.scope == _SCOPE_INFLIGHT,
            AuthAttempt.seen_values == token,
        ).delete(synchronize_session=False)
        db.session.commit()

    try:
        _run(op)
    except _StoreUnavailable:
        return


def _claim_slot(slot, token, now, expires):
    """Atomically take one numbered slot. ``None`` means the table is absent."""
    for _ in range(_RETRIES):
        try:
            claimed = _cas_expired_slot(slot, token, now, expires)
        except OperationalError as exc:
            if not _retryable_database_error(exc):
                raise
            continue
        if claimed is None:
            return None
        if claimed:
            return True
        try:
            inserted = _insert(
                _SCOPE_INFLIGHT, slot, failures=0, lockouts=0,
                updated_at=now, locked_until=expires, seen_values=token)
        except OperationalError as exc:
            if not _retryable_database_error(exc):
                raise
            continue
        if inserted is None:
            return None
        if inserted:
            return True
        # The unique index already has an owner. Reclaim it only when the
        # lease stored on that row has ended.
        try:
            claimed = _cas_expired_slot(slot, token, now, expires)
        except OperationalError as exc:
            if not _retryable_database_error(exc):
                raise
            continue
        if claimed is None:
            return None
        return bool(claimed)
    return False


def _cas_expired_slot(slot, token, now, expires):
    """Take a slot whose own lease has ended. The row lock decides the winner."""
    db, AuthAttempt = _models()

    def op():
        updated = db.session.query(AuthAttempt).filter(
            AuthAttempt.scope == _SCOPE_INFLIGHT,
            AuthAttempt.subject == slot,
            db.or_(
                AuthAttempt.locked_until.is_(None),
                AuthAttempt.locked_until <= now,
            ),
        ).update({
            AuthAttempt.locked_until: expires,
            AuthAttempt.updated_at: now,
            AuthAttempt.seen_values: token,
            AuthAttempt.failures: 0,
            AuthAttempt.lockouts: 0,
        }, synchronize_session=False)
        db.session.commit()
        return updated == 1

    try:
        return bool(_run(op))
    except _StoreUnavailable:
        return None


def _retryable_database_error(exc):
    message = str(getattr(exc, 'orig', exc)).lower()
    return (
        'database is locked' in message
        or 'deadlock' in message
        or 'try restarting transaction' in message
    )


def _expire_inflight(now):
    """Delete slots whose own lease has ended, including a legacy counter row."""
    db, AuthAttempt = _models()

    def op():
        db.session.query(AuthAttempt).filter(
            AuthAttempt.scope == _SCOPE_INFLIGHT,
            db.or_(
                AuthAttempt.locked_until.is_(None),
                AuthAttempt.locked_until <= now,
            ),
        ).delete(synchronize_session=False)
        db.session.commit()
        return True

    try:
        return _run(op)
    except _StoreUnavailable:
        return _MISSING


def _record(source, username, malformed):
    _prune()
    scopes = [('source', source, _setting('AUTH_SOURCE_LIMIT', _SOURCE_LIMIT),
               _setting('AUTH_SOURCE_WINDOW', _SOURCE_WINDOW),
               'malformed' if malformed else username)]
    if username and not malformed:
        scopes.append((
            'account', username,
            _setting('AUTH_ACCOUNT_LIMIT', _ACCOUNT_LIMIT),
            _setting('AUTH_ACCOUNT_WINDOW', _ACCOUNT_WINDOW),
            source,
        ))
        scopes.append((
            'pair', _pair_subject(source, username),
            _setting('AUTH_PAIR_LIMIT', _PAIR_LIMIT),
            _setting('AUTH_PAIR_WINDOW', _PAIR_WINDOW),
            None,
        ))
    retry = None
    for scope, subject, limit, window, seen in scopes:
        outcome = _bump(scope, subject, limit, window, seen, source, username)
        if outcome and outcome > (retry or 0):
            retry = outcome
    return retry


def _bump(scope, subject, limit, window_seconds, seen_item, source, username):
    for _ in range(_RETRIES):
        now = _now()
        row = _load(scope, subject)
        if row is _MISSING:
            return None
        if row is None:
            seen, crossed = _merge_seen(None, seen_item)
            inserted = _insert(
                scope, subject, failures=1, lockouts=0,
                window_started=now, updated_at=now,
                seen_values=json.dumps(seen))
            if inserted is None:
                return None
            if not inserted:
                continue
            _alert_seen(scope, source, username, len(seen), crossed)
            if 1 >= limit:
                return _start_lock_on_new_row(
                    scope, subject, source, username)
            return None
        if row.locked_until and row.locked_until > now:
            return _seconds_until(row.locked_until, now)
        failures = row.failures
        window = row.window_started or now
        if (now - window).total_seconds() >= window_seconds:
            failures = 0
            window = now
        failures += 1
        lockouts = row.lockouts
        locked_until = None
        if failures >= limit:
            lockouts += 1
            failures = limit
            locked_until = now + timedelta(seconds=_cooldown(lockouts))
        seen, crossed = _merge_seen(row.seen_values, seen_item)
        wrote = _compare(row, {
            'failures': failures,
            'lockouts': lockouts,
            'window_started': window,
            'locked_until': locked_until,
            'seen_values': json.dumps(seen),
            'updated_at': now,
        })
        if not wrote:
            continue
        _alert_seen(scope, source, username, len(seen), crossed)
        if locked_until:
            current_app.logger.warning(
                'Authentication throttled for %s %s after %s failures; '
                'retry after %s seconds',
                scope, subject, failures,
                _seconds_until(locked_until, now))
            return _seconds_until(locked_until, now)
        return None
    current_app.logger.error(
        'Authentication throttle update failed for %s %s', scope, subject)
    return 1


def _start_lock_on_new_row(scope, subject, source, username):
    """The first failure already met a limit of one. Lock that new row."""
    now = _now()
    locked_until = now + timedelta(seconds=_cooldown(1))
    row = _load(scope, subject)
    if row is None:
        return _cooldown(1)
    if _compare(row, {
            'failures': 1,
            'lockouts': 1,
            'locked_until': locked_until,
            'updated_at': now,
    }):
        current_app.logger.warning(
            'Authentication throttled for %s %s after %s failures; '
            'retry after %s seconds',
            scope, subject, 1, _seconds_until(locked_until, now))
    fresh = _load(scope, subject)
    if fresh and fresh.locked_until and fresh.locked_until > _now():
        return _seconds_until(fresh.locked_until, _now())
    return None


def _alert_seen(scope, source, username, count, crossed):
    if not crossed:
        return
    if (scope == 'source' and username and username != 'malformed'
            and count >= _setting('AUTH_SPRAY_USERNAMES', _SPRAY_USERNAMES)):
        current_app.logger.warning(
            'Authentication spray from %s tried %s distinct usernames',
            source, count)
    elif (scope == 'account' and username
            and count >= _setting('AUTH_SPRAY_SOURCES', _SPRAY_SOURCES)):
        current_app.logger.warning(
            'Authentication spray against %s came from %s distinct sources',
            username, count)


def _failures(scope, subject):
    row = _load(scope, subject)
    if row is None or row is _MISSING:
        return 0
    return row.failures or 0


def _clear(scope, subject):
    db, AuthAttempt = _models()

    def op():
        db.session.query(AuthAttempt).filter(
            AuthAttempt.scope == scope,
            AuthAttempt.subject == subject,
        ).update({
            AuthAttempt.failures: 0,
            AuthAttempt.lockouts: 0,
            AuthAttempt.locked_until: None,
            AuthAttempt.window_started: None,
        }, synchronize_session=False)
        db.session.commit()

    try:
        _run(op)
    except _StoreUnavailable:
        return


def _keys(source, username):
    yield 'source', source
    if username:
        yield 'account', username
        yield 'pair', _pair_subject(source, username)


def _pair_subject(source, username):
    return '{0}|{1}'.format(source, username)[:160]


def _cooldown(level):
    configured = current_app.config.get('AUTH_COOLDOWN_SECONDS') or _COOLDOWNS
    try:
        steps = tuple(int(item) for item in configured)
    except (TypeError, ValueError):
        steps = _COOLDOWNS
    if not steps:
        steps = _COOLDOWNS
    index = max(int(level), 1) - 1
    if index >= len(steps):
        return steps[-1]
    return max(1, steps[index])


def _setting(name, default):
    try:
        value = int(current_app.config.get(name, default))
    except (TypeError, ValueError):
        return default
    return max(1, value)


def _load(scope, subject):
    db, AuthAttempt = _models()

    def op():
        return db.session.query(AuthAttempt).filter(
            AuthAttempt.scope == scope,
            AuthAttempt.subject == subject,
        ).one_or_none()

    try:
        return _run(op)
    except _StoreUnavailable:
        return _MISSING


def _insert(scope, subject, **fields):
    db, AuthAttempt = _models()

    def op():
        row = AuthAttempt(scope=scope, subject=subject, **fields)
        db.session.add(row)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return False
        return True

    try:
        wrote = _run(op)
    except _StoreUnavailable:
        return None
    return bool(wrote)


def _compare(row, values, match_updated=False):
    db, AuthAttempt = _models()
    filters = [
        AuthAttempt.id == row.id,
        AuthAttempt.failures == row.failures,
        AuthAttempt.lockouts == row.lockouts,
    ]
    if match_updated:
        filters.append(AuthAttempt.updated_at == row.updated_at)
    else:
        if row.locked_until is None:
            filters.append(AuthAttempt.locked_until.is_(None))
        else:
            filters.append(AuthAttempt.locked_until == row.locked_until)

    def op():
        updated = db.session.query(AuthAttempt).filter(*filters).update(
            values, synchronize_session=False)
        db.session.commit()
        return updated == 1

    return bool(_run(op))


def _prune():
    db, AuthAttempt = _models()
    cutoff = _now() - _PRUNE_AFTER

    def op():
        stale = db.session.query(AuthAttempt.id).filter(
            AuthAttempt.scope != _SCOPE_INFLIGHT,
            AuthAttempt.updated_at < cutoff,
            db.or_(
                AuthAttempt.locked_until.is_(None),
                AuthAttempt.locked_until < _now(),
            ),
        ).limit(100).all()
        if not stale:
            return
        db.session.query(AuthAttempt).filter(
            AuthAttempt.id.in_([item.id for item in stale])
        ).delete(synchronize_session=False)
        db.session.commit()

    try:
        _run(op)
    except _StoreUnavailable:
        return


class _StoreUnavailable(Exception):
    pass


def _run(operation):
    global _logged_missing_table
    try:
        return operation()
    except (OperationalError, ProgrammingError, RuntimeError) as exc:
        try:
            from ..models.base import db
            db.session.rollback()
        except Exception:
            pass
        if _missing_table(exc) or _store_unready(exc):
            if not _logged_missing_table and not current_app.config.get('TESTING'):
                _logged_missing_table = True
                current_app.logger.error(
                    'Authentication throttling is unavailable because '
                    'the auth_attempt table is missing.')
            raise _StoreUnavailable()
        raise


def _store_unready(exc):
    """True when this process has no database to share the counters."""
    return 'not registered with this' in str(exc).lower()


def _missing_table(exc):
    message = str(getattr(exc, 'orig', exc)).lower()
    return (
        "doesn't exist" in message
        or 'no such table' in message
        or '1146' in message
    )


def _models():
    from ..models.auth_attempt import AuthAttempt
    from ..models.base import db
    return db, AuthAttempt


def _merge_seen(raw, item):
    try:
        seen = json.loads(raw) if raw else []
    except (TypeError, ValueError):
        seen = []
    if not isinstance(seen, list):
        seen = []
    seen = [str(value)[:_USERNAME_LIMIT] for value in seen][:_SEEN_CAP]
    if not item or item in seen or len(seen) >= _SEEN_CAP:
        return seen, False
    seen.append(str(item)[:_USERNAME_LIMIT])
    threshold = item != 'malformed' and (
        len(seen) == _setting('AUTH_SPRAY_USERNAMES', _SPRAY_USERNAMES)
        or len(seen) == _setting('AUTH_SPRAY_SOURCES', _SPRAY_SOURCES)
    )
    return seen, threshold


def _direct_peer():
    original = request.environ.get('werkzeug.proxy_fix.orig') or {}
    peer = original.get('REMOTE_ADDR') or request.environ.get('REMOTE_ADDR')
    return _parse_ip(peer)


def _forwarded_addresses():
    addresses = []
    for header in request.headers.getlist('X-Forwarded-For'):
        for part in header.split(','):
            parsed = _parse_ip(part)
            if parsed is not None:
                addresses.append(parsed)
    return addresses


def _trusted_networks():
    raw = current_app.config.get('AUTH_TRUSTED_PROXIES') or []
    if isinstance(raw, str):
        raw = [item.strip() for item in raw.split(',') if item.strip()]
    networks = []
    for item in raw:
        try:
            networks.append(ipaddress.ip_network(str(item), strict=False))
        except ValueError:
            continue
    return networks


def _in_networks(address, networks):
    return any(address in network for network in networks)


def _parse_ip(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text or len(text) > 64:
        return None
    try:
        return ipaddress.ip_address(text)
    except ValueError:
        return None


def _bounded_text(value, limit):
    if value is None:
        return ''
    if not isinstance(value, str):
        return None
    if '\x00' in value or len(value) > limit:
        return None
    return value.strip()


def _now():
    return datetime.utcnow().replace(microsecond=0)


def _seconds_until(locked_until, now):
    return max(1, int((locked_until - now).total_seconds()))
