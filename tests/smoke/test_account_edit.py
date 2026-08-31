import re

from powerdnsadmin.models.account import Account
from powerdnsadmin.models.base import db
from powerdnsadmin.models.domain import Domain
from powerdnsadmin.models.user import User


def csrf_token(response):
    match = re.search(
        rb'name="_csrf_token" value="([^"]+)"',
        response.data,
    )
    assert match is not None, 'account edit form is missing a CSRF token'
    return match.group(1).decode('utf-8')


def test_edit_account_assigns_domain_and_user_without_posted_account_name(
        app, logged_in_admin_client, monkeypatch):
    submitted_account_name = 'account-edit-regression'
    domain_name = 'account-edit-regression.example'

    with app.app_context():
        account = Account(
            name=submitted_account_name,
            description='Original description',
            contact='Original contact',
            mail='original@example.com',
        )
        assert account.create_account()['status']
        account_name = account.name
        db.session.add(Domain(name=domain_name))
        db.session.commit()

    associated_account_ids = []

    def associate_account(domain, account_id, update=True):
        associated_account_ids.append(account_id)
        stored_domain = Domain.query.filter_by(name=domain.name).one()
        stored_domain.account_id = account_id
        db.session.commit()
        return {'status': 'ok', 'msg': 'account changed successfully'}

    monkeypatch.setattr(Domain, 'assoc_account', associate_account)

    edit_page = logged_in_admin_client.get(
        '/admin/account/edit/{}'.format(account_name))
    assert edit_page.status_code == 200

    response = logged_in_admin_client.post(
        '/admin/account/edit/{}'.format(account_name),
        data={
            '_csrf_token': csrf_token(edit_page),
            'create': '0',
            'accountdescription': 'Updated description',
            'accountcontact': 'Updated contact',
            'accountmail': 'updated@example.com',
            'account_multi_user': app.config['TEST_USER'],
            'account_domains': domain_name,
        },
    )

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/admin/manage-account')

    with app.app_context():
        stored_account = Account.query.filter_by(name=account_name).one()
        stored_domain = Domain.query.filter_by(name=domain_name).one()
        stored_user = User.query.filter_by(
            username=app.config['TEST_USER']).one()
        assert stored_account.description == 'Updated description'
        assert stored_domain.account_id == stored_account.id
        assert stored_account.get_user() == [stored_user.id]
        assert associated_account_ids == [stored_account.id]
