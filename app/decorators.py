from functools import wraps
from flask import g, request, redirect, url_for

from app import app
from app.models import Role


def admin_role_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.role.name != 'Administrator':
            return redirect(url_for('error', code=401))
        return f(*args, **kwargs)
    return decorated_function


def can_access_domain(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.role.name != 'Administrator':
            domain_name = kwargs.get('domain_name')
            user_domain = [d.name for d in g.user.get_domain()]

            if domain_name not in user_domain:
                return redirect(url_for('error', code=401))

        return f(*args, **kwargs)
    return decorated_function


def can_configure_dnssec(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.role.name != 'Administrator' and app.config['DNSSEC_ADMINS_ONLY']:
                return redirect(url_for('error', code=401))

        return f(*args, **kwargs)
    return decorated_function
