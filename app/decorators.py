from functools import wraps
from flask import g, redirect, url_for

from app.models import Setting


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
