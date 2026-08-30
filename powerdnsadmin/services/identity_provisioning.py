"""Shared JIT account and role provisioning for federated identities."""

from ..models.account import Account
from ..models.history import History
from ..models.role import Role


def record_user_creation(user, *, audit_actor):
    History(msg='Created user {0}'.format(user.username),
            created_by=audit_actor).add()


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
    if user.role.name != 'Administrator':
        user.role_id = Role.query.filter_by(name='Administrator').first().id
        history = History(msg='Promoting {0} to administrator'.format(
            user.username),
            created_by=audit_actor)
        history.add()


def uplift_to_operator(user, *, audit_actor):
    if user.role.name != 'Operator':
        user.role_id = Role.query.filter_by(name='Operator').first().id
        history = History(msg='Promoting {0} to operator'.format(
            user.username),
            created_by=audit_actor)
        history.add()


def demote_to_user(user, *, audit_actor):
    if user.role.name != 'User':
        user.role_id = Role.query.filter_by(name='User').first().id
        history = History(msg='Demoting {0} to user'.format(user.username),
                          created_by=audit_actor)
        history.add()
