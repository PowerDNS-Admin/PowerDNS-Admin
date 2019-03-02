from functools import wraps
from flask import g, redirect, url_for, request, abort

from app.models import Setting
from .models import User, ApiKey
import base64
from app.lib.log import logging
from app.errors import RequestIsNotJSON, NotEnoughPrivileges
from app.errors import DomainAccessForbidden


def admin_role_required(f):
    """
    Grant access if user is in Administrator role
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.role.name != 'Administrator':
            return redirect(url_for('error', code=401))
        return f(*args, **kwargs)
    return decorated_function


def operator_role_required(f):
    """
    Grant access if user is in Operator role or higher
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.role.name not in ['Administrator', 'Operator']:
            return redirect(url_for('error', code=401))
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
        if g.user.role.name not in ['Administrator', 'Operator']:
            domain_name = kwargs.get('domain_name')
            user_domain = [d.name for d in g.user.get_domain()]

            if domain_name not in user_domain:
                return redirect(url_for('error', code=401))

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
        if g.user.role.name not in ['Administrator', 'Operator'] and Setting().get('dnssec_admins_only'):
            return redirect(url_for('error', code=401))

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
        if g.user.role.name not in ['Administrator', 'Operator'] and not Setting().get('allow_user_create_domain'):
            return redirect(url_for('error', code=401))
        return f(*args, **kwargs)
    return decorated_function


def api_basic_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            auth_header = auth_header.replace('Basic ', '', 1)

            try:
                auth_header = str(base64.b64decode(auth_header), 'utf-8')
                username, password = auth_header.split(":")
            except TypeError as e:
                logging.error('Error: {0}'.format(e))
                abort(401)

            user = User(
                username=username,
                password=password,
                plain_text_password=password
            )

            try:
                auth_method = request.args.get('auth_method', 'LOCAL')
                auth_method = 'LDAP' if auth_method != 'LOCAL' else 'LOCAL'
                auth = user.is_validate(
                    method=auth_method,
                    src_ip=request.remote_addr
                )

                if not auth:
                    logging.error('Checking user password failed')
                    abort(401)
                else:
                    user = User.query.filter(User.username == username).first()
                    g.user = user
            except Exception as e:
                logging.error('Error: {0}'.format(e))
                abort(401)
        else:
            logging.error('Error: Authorization header missing!')
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

def api_can_create_domain(f):
    """
    Grant access if:
        - user is in Operator role or higher, or
        - allow_user_create_domain is on
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.role.name not in ['Administrator', 'Operator'] and not Setting().get('allow_user_create_domain'):
            msg = "User {0} does not have enough privileges to create domain"
            logging.error(msg.format(g.user.username))
            raise NotEnoughPrivileges()
        return f(*args, **kwargs)
    return decorated_function


def apikey_is_admin(f):
    """
    Grant access if user is in Administrator role
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.apikey.role.name != 'Administrator':
            msg = "Apikey {0} does not have enough privileges to create domain"
            logging.error(msg.format(g.apikey.id))
            raise NotEnoughPrivileges()
        return f(*args, **kwargs)
    return decorated_function


def apikey_can_access_domain(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        apikey = g.apikey
        if g.apikey.role.name not in ['Administrator', 'Operator']:
            domains = apikey.domains
            zone_id = kwargs.get('zone_id')
            domain_names = [item.name for item in domains]

            if zone_id not in domain_names:
                raise DomainAccessForbidden()
        return f(*args, **kwargs)
    return decorated_function


def apikey_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('X-API-KEY')
        if auth_header:
            try:
                apikey_val = str(base64.b64decode(auth_header), 'utf-8')
            except TypeError as e:
                logging.error('Error: {0}'.format(e))
                abort(401)

            apikey = ApiKey(
                key=apikey_val
            )
            apikey.plain_text_password = apikey_val

            try:
                auth_method = 'LOCAL'
                auth = apikey.is_validate(
                    method=auth_method,
                    src_ip=request.remote_addr
                )

                g.apikey = auth
            except Exception as e:
                logging.error('Error: {0}'.format(e))
                abort(401)
        else:
            logging.error('Error: API key header missing!')
            abort(401)

        return f(*args, **kwargs)
    return decorated_function
