import base64
import binascii
from functools import wraps
from flask import g, request, abort, current_app, Response
from flask_login import current_user

from .models import User, ApiKey, Setting, Domain, Setting
from .lib.errors import RequestIsNotJSON, NotEnoughPrivileges, RecordTTLNotAllowed, RecordTypeNotAllowed
from .lib.errors import DomainAccessForbidden, DomainOverrideForbidden


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


def api_basic_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            current_app.logger.error('Error: Authorization header missing!')
            abort(401)

        if auth_header[:6] != "Basic ":
            current_app.logger.error('Error: Unsupported authorization mechanism!')
            abort(401)

        # Remove "Basic " from the header value
        auth_header = auth_header[6:]
        auth_components = []

        try:
            auth_header = str(base64.b64decode(auth_header), 'utf-8')
            # NK: We use auth_components here as we don't know if we'll have a colon,
            # we split it maximum 1 times to grab the username, the rest of the string would be the password.
            auth_components = auth_header.split(':', maxsplit=1)
        except (binascii.Error, UnicodeDecodeError) as e:
            current_app.logger.error(
                'Invalid base64-encoded of credential. Error {0}'.format(
                    e))
            abort(401)
        except TypeError as e:
            current_app.logger.error('Error: {0}'.format(e))
            abort(401)

        # If we don't have two auth components (username, password), we can abort
        if len(auth_components) != 2:
            abort(401)

        (username, password) = auth_components

        user = User(username=username,
                    password=password,
                    plain_text_password=password)

        try:
            if Setting().get('verify_user_email') and user.email and not user.confirmed:
                current_app.logger.warning(
                    'Basic authentication failed for user {} because of unverified email address'
                    .format(username))
                abort(401)

            auth_method = request.args.get('auth_method', 'LOCAL')
            auth_method = 'LDAP' if auth_method != 'LOCAL' else 'LOCAL'
            auth = user.is_validate(method=auth_method, src_ip=request.remote_addr)

            if not auth:
                current_app.logger.error('Checking user password failed')
                abort(401)
            else:
                user = User.query.filter(User.username == username).first()
                current_user = user  # lgtm [py/unused-local-variable]
        except Exception as e:
            current_app.logger.error('Error: {0}'.format(e))
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
            try:
                user_id = int(kwargs.get('user_id'))
            except:
                user_id = None
            try:
                username = kwargs.get('username')
            except:
                username = None
            if (
                    (current_user.role.name in roles) or
                    (allow_self and user_id and current_user.id == user_id) or
                    (allow_self and username and current_user.username == username)
            ):
                return f(*args, **kwargs)
            msg = (
                "User {} with role {} does not have enough privileges to {}"
            ).format(current_user.username, current_user.role.name, action)
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
        if current_user.role.name not in [
            'Administrator', 'Operator'
        ] and not Setting().get('allow_user_create_domain'):
            msg = "User {0} does not have enough privileges to create zone"
            current_app.logger.error(msg.format(current_user.username))
            raise NotEnoughPrivileges()

        if Setting().get('deny_domain_override'):
            req = request.get_json(force=True)
            domain = Domain()
            if req['name'] and domain.is_overriding(req['name']):
                raise DomainOverrideForbidden()

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
        if g.apikey.role.name not in ['Administrator', 'Operator']:
            zone_id = kwargs.get('zone_id').rstrip(".")
            domain_names = [item.name for item in g.apikey.domains]

            accounts = g.apikey.accounts
            accounts_domains = [domain.name for a in accounts for domain in a.domains]

            allowed_domains = set(domain_names + accounts_domains)

            if zone_id not in allowed_domains:
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
        auth_header = request.headers.get('X-API-KEY')
        if auth_header:
            try:
                apikey_val = str(base64.b64decode(auth_header), 'utf-8')
            except (binascii.Error, UnicodeDecodeError) as e:
                current_app.logger.error('Invalid base64-encoded X-API-KEY. Error {0}'.format(e))
                abort(401)
            except TypeError as e:
                current_app.logger.error('Error: {0}'.format(e))
                abort(401)

            apikey = ApiKey(key=apikey_val)
            apikey.plain_text_password = apikey_val

            try:
                auth_method = 'LOCAL'
                auth = apikey.is_validate(method=auth_method,
                                          src_ip=request.remote_addr)

                g.apikey = auth
            except Exception as e:
                current_app.logger.error('Error: {0}'.format(e))
                abort(401)
        else:
            current_app.logger.error('Error: API key header missing!')
            abort(401)

        return f(*args, **kwargs)

    return decorated_function


def dyndns_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated is False:
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
