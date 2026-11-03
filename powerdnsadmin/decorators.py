import base64
import binascii
from functools import wraps
from flask import g, request, abort, current_app, Response
from werkzeug.exceptions import TooManyRequests
from flask_login import AnonymousUserMixin, current_user

from .models import User, ApiKey, Setting, Domain, Setting
from .lib.errors import RequestIsNotJSON, NotEnoughPrivileges, RecordTTLNotAllowed, RecordTypeNotAllowed
from .lib.errors import DomainAccessForbidden, DomainOverrideForbidden
from .lib.helper import (
    UpstreamPathRejected, apikey_can_reach_zone, canonical_request_path,
    zone_from_path)
from .lib.password_login import otp_login_blocked, password_login_blocked
from .lib.auth_throttle import (
    THROTTLE_MESSAGE, AuthenticationThrottled, ThrottleStoreUnavailable,
    active_retry_after, api_key_bounded, api_key_retry_after,
    authentication_source, claim_api_key_slot, credentials_bounded,
    note_rejected_api_key, record_malformed, release_inflight)


def api_authenticated_user():
    """
    Return the user authenticated by this request's Basic credentials.

    The API before_request runs before those credentials are checked. Falling
    back to Flask-Login's current_user there loads a remember-me cookie into
    the server session and saves it, which is how a published SECRET_KEY
    became a long-lived Administrator session.
    """
    return getattr(g, 'basic_auth_user', None) or AnonymousUserMixin()


def admin_role_required(f):
    """
    Grant access if user is in Administrator role
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role.name != 'Administrator':
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def operator_role_required(f):
    """
    Grant access if user is in Operator role or higher
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role.name not in ['Administrator', 'Operator']:
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def history_access_required(f):
    """
    Grant access if user is in Operator role or higher, or Users can view history
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role.name not in [
            'Administrator', 'Operator'
        ] and not Setting().get('allow_user_view_history'):
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def can_access_domain(f):
    """
    Grant access if:
        - user is in Operator role or higher, or
        - user is in granted Account, or
        - user is in granted Domain
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role.name not in ['Administrator', 'Operator']:
            domain_name = kwargs.get('domain_name')
            domain = Domain.query.filter(Domain.name == domain_name).first()

            if not domain:
                abort(404)

            valid_access = Domain(id=domain.id).is_valid_access(
                current_user.id)

            if not valid_access:
                abort(403)

        return f(*args, **kwargs)

    return decorated_function


def can_configure_dnssec(f):
    """
    Grant access if:
        - user is in Operator role or higher, or
        - dnssec_admins_only is off
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role.name not in [
            'Administrator', 'Operator'
        ] and Setting().get('dnssec_admins_only'):
            abort(403)

        return f(*args, **kwargs)

    return decorated_function


def can_remove_domain(f):
    """
    Grant access if:
        - user is in Operator role or higher, or
        - allow_user_remove_domain is on
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role.name not in [
            'Administrator', 'Operator'
        ] and not Setting().get('allow_user_remove_domain'):
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def can_create_domain(f):
    """
    Grant access if:
        - user is in Operator role or higher, or
        - allow_user_create_domain is on
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role.name not in [
            'Administrator', 'Operator'
        ] and not Setting().get('allow_user_create_domain'):
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def _remember_throttle(exc):
    g.auth_throttled = exc
    return None


def _throttle_malformed_basic():
    try:
        retry = record_malformed(authentication_source())
    except AuthenticationThrottled as exc:
        return _remember_throttle(exc)
    if retry:
        return _remember_throttle(AuthenticationThrottled(retry))
    return None


def accept_basic_credentials():
    """Return the user authenticated by this request's Basic credentials.

    The login form, this function, and the browser request loader share
    ``password_login_blocked`` and ``otp_login_blocked``. An account with a
    TOTP secret must also send that code in the ``X-OTP`` header. API keys
    do not come through here.
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    if len(auth_header) > 1024 or auth_header[:6] != "Basic ":
        current_app.logger.error('Error: Unsupported authorization mechanism!')
        return _throttle_malformed_basic()

    auth_header = auth_header[6:]
    try:
        auth_header = str(base64.b64decode(auth_header), 'utf-8')
        auth_components = auth_header.split(':', maxsplit=1)
    except (binascii.Error, UnicodeDecodeError) as e:
        current_app.logger.error(
            'Invalid base64-encoded of credential. Error {0}'.format(e))
        return _throttle_malformed_basic()
    except TypeError as e:
        current_app.logger.error('Error: {0}'.format(e))
        return _throttle_malformed_basic()

    if len(auth_components) != 2:
        return _throttle_malformed_basic()

    (username, password) = auth_components
    if not credentials_bounded(username, password):
        return _throttle_malformed_basic()
    retry = active_retry_after(authentication_source(), username)
    if retry:
        return _remember_throttle(AuthenticationThrottled(retry))
    auth_method = request.args.get('auth_method', 'LOCAL')
    auth_method = 'LDAP' if auth_method != 'LOCAL' else 'LOCAL'
    user = User(username=username,
                password=password,
                plain_text_password=password)
    blocked = password_login_blocked(
        user,
        auth_method,
        local_db_enabled=Setting().get('local_db_enabled'),
        verify_user_email=Setting().get('verify_user_email'),
    )
    if blocked:
        current_app.logger.warning(
            'Basic authentication rejected for user {0}: {1}'.format(
                username, blocked))
        return None

    try:
        auth = user.is_validate(method=auth_method, src_ip=request.remote_addr)
    except AuthenticationThrottled as exc:
        return _remember_throttle(exc)
    except ThrottleStoreUnavailable:
        raise
    except Exception as e:
        current_app.logger.error('Error: {0}'.format(e))
        return None
    if not auth:
        current_app.logger.error('Checking user password failed')
        return None

    blocked = otp_login_blocked(user, request.headers.get('X-OTP'))
    if blocked:
        current_app.logger.warning(
            'Basic authentication rejected for user {0}: {1}'.format(
                username, blocked))
        return None
    return User.query.filter(User.username == username).first()


def _api_key_throttled(retry_after):
    return _remember_throttle(AuthenticationThrottled(retry_after))


def _spend_api_key_failure(source):
    """Count one rejected key. A closed budget becomes HTTP 429."""
    retry = note_rejected_api_key(source)
    if retry:
        return _api_key_throttled(retry)
    return None


def accept_api_key():
    """Return the API key authenticated by ``X-API-KEY``, or ``None``.

    The source budget is checked before bcrypt. Invalid, malformed, and
    oversized keys spend that source only. Password and one-time-code
    counters are left untouched, and the raw token is not logged.
    """
    auth_header = request.headers.get('X-API-KEY')
    if not auth_header:
        return None
    source = authentication_source()
    retry = api_key_retry_after(source)
    if retry:
        return _api_key_throttled(retry)
    if len(auth_header) > 1024:
        current_app.logger.warning('Rejected oversized API key from %s', source)
        return _spend_api_key_failure(source)
    try:
        apikey_val = str(base64.b64decode(auth_header), 'utf-8')
    except (binascii.Error, UnicodeDecodeError):
        current_app.logger.warning('Rejected malformed API key from %s', source)
        return _spend_api_key_failure(source)
    except TypeError:
        current_app.logger.warning('Rejected malformed API key from %s', source)
        return _spend_api_key_failure(source)
    if not api_key_bounded(apikey_val):
        current_app.logger.warning('Rejected malformed API key from %s', source)
        return _spend_api_key_failure(source)

    lease = claim_api_key_slot()
    if lease is False:
        return _api_key_throttled(1)
    try:
        apikey = ApiKey(key=apikey_val)
        apikey.plain_text_password = apikey_val
        try:
            return apikey.is_validate(
                method='LOCAL', src_ip=request.remote_addr)
        except Exception:
            current_app.logger.warning('Rejected API key from %s', source)
            return _spend_api_key_failure(source)
    finally:
        if lease:
            release_inflight(lease)


def establish_api_identity():
    """Authenticate an API request once, before maintenance checks run.

    View decorators call this too. The second call does not check the
    password or the one-time code again, so a TOTP code is not consumed twice.
    """
    if getattr(g, '_api_identity_ready', False):
        return
    g._api_identity_ready = True
    if request.headers.get('X-API-KEY'):
        apikey = accept_api_key()
        throttled = getattr(g, 'auth_throttled', None)
        if throttled is not None:
            error = TooManyRequests(THROTTLE_MESSAGE)
            error.retry_after = throttled.retry_after
            raise error
        if apikey is None:
            abort(401)
        g.apikey = apikey
        return
    if request.headers.get('Authorization'):
        user = accept_basic_credentials()
        throttled = getattr(g, 'auth_throttled', None)
        if throttled is not None:
            error = TooManyRequests(THROTTLE_MESSAGE)
            error.retry_after = throttled.retry_after
            raise error
        if user is None:
            abort(401)
        g.basic_auth_user = user


def api_basic_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        establish_api_identity()
        if getattr(g, 'basic_auth_user', None) is None:
            if not request.headers.get('Authorization'):
                current_app.logger.error('Error: Authorization header missing!')
            abort(401)
        return f(*args, **kwargs)

    return decorated_function


def is_json(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH']:
            if not request.is_json:
                raise RequestIsNotJSON()
        return f(*args, **kwargs)

    return decorated_function


def callback_if_request_body_contains_key(callback, http_methods=[], keys=[]):
    """
    If request body contains one or more of specified keys, call
    :param callback
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            check_current_http_method = not http_methods or request.method in http_methods
            if (check_current_http_method and
                    set(request.get_json(force=True).keys()).intersection(set(keys))
            ):
                callback(*args, **kwargs)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def api_role_can(action, roles=None, allow_self=False):
    """
    Grant access if:
        - user is in the permitted roles
        - allow_self and kwargs['user_id'] = current_user.id
        - allow_self and kwargs['username'] = current_user.username
    """
    if roles is None:
        roles = ['Administrator', 'Operator']

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            authenticated_user = api_authenticated_user()
            try:
                user_id = int(kwargs.get('user_id'))
            except:
                user_id = None
            try:
                username = kwargs.get('username')
            except:
                username = None
            if (
                    (authenticated_user.role.name in roles) or
                    (allow_self and user_id and
                     authenticated_user.id == user_id) or
                    (allow_self and username and
                     authenticated_user.username == username)
            ):
                return f(*args, **kwargs)
            msg = (
                "User {} with role {} does not have enough privileges to {}"
            ).format(authenticated_user.username,
                     authenticated_user.role.name, action)
            raise NotEnoughPrivileges(message=msg)

        return decorated_function

    return decorator


def api_can_create_domain(f):
    """
    Grant access if:
        - user is in Operator role or higher, or
        - allow_user_create_domain is on
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        authenticated_user = api_authenticated_user()
        if authenticated_user.role.name not in [
            'Administrator', 'Operator'
        ] and not Setting().get('allow_user_create_domain'):
            msg = "User {0} does not have enough privileges to create zone"
            current_app.logger.error(
                msg.format(authenticated_user.username))
            raise NotEnoughPrivileges()

        if Setting().get('deny_domain_override'):
            req = request.get_json(force=True)
            domain = Domain()
            if req['name'] and domain.is_overriding(req['name']):
                raise DomainOverrideForbidden()

        return f(*args, **kwargs)

    return decorated_function


def api_can_remove_domain(f):
    """
    Grant API access if the Basic-authenticated user is an Operator or higher,
    or ordinary-user zone removal is enabled.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        authenticated_user = api_authenticated_user()
        if (authenticated_user.role.name not in [
                'Administrator', 'Operator'
        ] and not Setting().get('allow_user_remove_domain')):
            msg = "User {0} does not have enough privileges to remove zone"
            current_app.logger.error(
                msg.format(authenticated_user.username))
            raise NotEnoughPrivileges()
        return f(*args, **kwargs)

    return decorated_function


def apikey_can_create_domain(f):
    """
    Grant access if:
        - user is in Operator role or higher, or
        - allow_user_create_domain is on
        and
        - deny_domain_override is off or
        - override_domain is true (from request)
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.apikey.role.name not in [
            'Administrator', 'Operator'
        ] and not Setting().get('allow_user_create_domain'):
            msg = "ApiKey #{0} does not have enough privileges to create zone"
            current_app.logger.error(msg.format(g.apikey.id))
            raise NotEnoughPrivileges()

        if Setting().get('deny_domain_override'):
            req = request.get_json(force=True)
            domain = Domain()
            if req['name'] and domain.is_overriding(req['name']):
                raise DomainOverrideForbidden()

        return f(*args, **kwargs)

    return decorated_function


def apikey_can_remove_domain(http_methods=[]):
    """
    Grant access if:
        - user is in Operator role or higher, or
        - allow_user_remove_domain is on
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            check_current_http_method = not http_methods or request.method in http_methods

            if (check_current_http_method and
                    g.apikey.role.name not in ['Administrator', 'Operator'] and
                    not Setting().get('allow_user_remove_domain')
            ):
                msg = "ApiKey #{0} does not have enough privileges to remove zone"
                current_app.logger.error(msg.format(g.apikey.id))
                raise NotEnoughPrivileges()
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def apikey_is_admin(f):
    """
    Grant access if user is in Administrator role
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.apikey.role.name != 'Administrator':
            msg = "Apikey {0} does not have enough privileges to create zone"
            current_app.logger.error(msg.format(g.apikey.id))
            raise NotEnoughPrivileges()
        return f(*args, **kwargs)

    return decorated_function


def apikey_can_access_domain(f):
    """
    Grant access if:
        - user has Operator role or higher, or
        - user has explicitly been granted access to domain
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            canonical_zone = zone_from_path(canonical_request_path())
        except UpstreamPathRejected:
            abort(400)
        route_zone = kwargs.get('zone_id')
        if isinstance(route_zone, str):
            route_zone = route_zone.rstrip('.')
        else:
            route_zone = None
        # The route parameter is the zone before ``..`` is normalized.
        # The zone that would be requested is the one that must be allowed.
        if (canonical_zone is not None and route_zone is not None
                and canonical_zone != route_zone):
            raise DomainAccessForbidden()
        zone_name = canonical_zone if canonical_zone is not None else route_zone
        if g.apikey.role.name not in ['Administrator', 'Operator']:
            if not zone_name or not apikey_can_reach_zone(zone_name):
                raise DomainAccessForbidden()
        return f(*args, **kwargs)

    return decorated_function


def apikey_can_configure_dnssec(http_methods=[]):
    """
    Grant access if:
        - user is in Operator role or higher, or
        - dnssec_admins_only is off
    """

    def decorator(f=None):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            check_current_http_method = not http_methods or request.method in http_methods

            if (check_current_http_method and
                    g.apikey.role.name not in ['Administrator', 'Operator'] and
                    Setting().get('dnssec_admins_only')
            ):
                msg = "ApiKey #{0} does not have enough privileges to configure dnssec"
                current_app.logger.error(msg.format(g.apikey.id))
                raise DomainAccessForbidden(message=msg)
            return f(*args, **kwargs) if f else None

        return decorated_function

    return decorator


def allowed_record_types(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['GET', 'DELETE', 'PUT']:
            return f(*args, **kwargs)

        if g.apikey.role.name in ['Administrator', 'Operator']:
            return f(*args, **kwargs)

        records_allowed_to_edit = Setting().get_records_allow_to_edit()
        content = request.get_json()
        try:
            for record in content['rrsets']:
                if 'type' not in record:
                    raise RecordTypeNotAllowed()

                if record['type'] not in records_allowed_to_edit:
                    current_app.logger.error(f"Error: Record type not allowed: {record['type']}")
                    raise RecordTypeNotAllowed(message=f"Record type not allowed: {record['type']}")
        except (TypeError, KeyError) as e:
            raise e
        return f(*args, **kwargs)

    return decorated_function


def allowed_record_ttl(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not Setting().get('enforce_api_ttl'):
            return f(*args, **kwargs)

        if request.method == 'GET':
            return f(*args, **kwargs)

        if g.apikey.role.name in ['Administrator', 'Operator']:
            return f(*args, **kwargs)

        allowed_ttls = Setting().get_ttl_options()
        allowed_numeric_ttls = [ttl[0] for ttl in allowed_ttls]
        content = request.get_json()
        try:
            for record in content['rrsets']:
                if 'ttl' not in record:
                    raise RecordTTLNotAllowed()

                if record['ttl'] not in allowed_numeric_ttls:
                    current_app.logger.error(f"Error: Record TTL not allowed: {record['ttl']}")
                    raise RecordTTLNotAllowed(message=f"Record TTL not allowed: {record['ttl']}")
        except (TypeError, KeyError) as e:
            raise e
        return f(*args, **kwargs)

    return decorated_function


def apikey_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        establish_api_identity()
        if getattr(g, 'apikey', None) is None:
            if not request.headers.get('X-API-KEY'):
                current_app.logger.error('Error: API key header missing!')
            abort(401)
        return f(*args, **kwargs)

    return decorated_function


def dyndns_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        authenticated = current_user.is_authenticated
        throttled = getattr(g, 'auth_throttled', None)
        if throttled is not None:
            response = Response(THROTTLE_MESSAGE + '\n', status=429)
            response.headers['Retry-After'] = str(throttled.retry_after)
            return response
        if authenticated is False:
            return Response(headers={'WWW-Authenticate': 'Basic'}, status=401)
        return f(*args, **kwargs)

    return decorated_function


def apikey_or_basic_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_auth_header = request.headers.get('X-API-KEY')
        if api_auth_header:
            return apikey_auth(f)(*args, **kwargs)
        else:
            return api_basic_auth(f)(*args, **kwargs)

    return decorated_function
