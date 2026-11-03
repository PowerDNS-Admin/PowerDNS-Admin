"""Shared JIT account and role provisioning for federated identities."""

from ..models.account import Account
from ..models.history import History
from ..models.role import Role
from ..routes.auth_session import record_user_event


def record_user_creation(user, *, audit_actor):
    record_user_event(
        'Created user {0}'.format(user.username),
        user.username,
        audit_actor,
    )


def handle_account(account_name, account_description="", *, audit_actor):
    clean_name = Account.sanitize_name(account_name)
    account = Account.query.filter_by(name=clean_name).first()
    if not account:
        account = Account(name=clean_name,
                          description=account_description,
                          contact='',
                          mail='')
        account.create_account()
        history = History(msg='Account {0} created'.format(account.name),
                          created_by=audit_actor)
        history.add()
    else:
        account.description = account_description
        account.update_account()
    return account


def uplift_to_admin(user, *, audit_actor):
    previous_role = user.role.name if user.role else None
    if previous_role != 'Administrator':
        user.role_id = Role.query.filter_by(name='Administrator').first().id
        record_user_event(
            'Promoting {0} to administrator'.format(user.username),
            user.username,
            audit_actor,
            role='Administrator',
            previous_role=previous_role,
        )


def uplift_to_operator(user, *, audit_actor):
    previous_role = user.role.name if user.role else None
    if previous_role != 'Operator':
        user.role_id = Role.query.filter_by(name='Operator').first().id
        record_user_event(
            'Promoting {0} to operator'.format(user.username),
            user.username,
            audit_actor,
            role='Operator',
            previous_role=previous_role,
        )


def demote_to_user(user, *, audit_actor):
    previous_role = user.role.name if user.role else None
    if previous_role != 'User':
        user.role_id = Role.query.filter_by(name='User').first().id
        record_user_event(
            'Demoting {0} to user'.format(user.username),
            user.username,
            audit_actor,
            role='User',
            previous_role=previous_role,
        )
