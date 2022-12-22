import json

from . import IntegrationApiManagement


class TestIntegrationApiManagementUser(IntegrationApiManagement):

    def test_accounts_empty_get(self, initial_data, client,  # noqa: F811
                                basic_auth_user_headers):  # noqa: F811
        res = client.get("/api/v1/pdnsadmin/accounts",
                         headers=basic_auth_user_headers)
        assert res.status_code == 401

    def test_users_empty_get(self, initial_data, client,  # noqa: F811
                             test_admin_user, test_user,  # noqa: F811
                             basic_auth_user_headers):  # noqa: F811
        res = client.get("/api/v1/pdnsadmin/users",
                         headers=basic_auth_user_headers)
        assert res.status_code == 401

    def test_self_get(self, initial_data, client, basic_auth_user_headers, test_user):  # noqa: F811
        res = client.get("/api/v1/pdnsadmin/users/{}".format(test_user),
                         headers=basic_auth_user_headers)
        data = res.get_json(force=True)
        assert res.status_code == 200
        assert data

    def test_create_account_fail(self, client, initial_data, account_data,  # noqa: F811
                                 basic_auth_user_headers):  # noqa: F811

        # Create account (should fail)
        res = client.post("/api/v1/pdnsadmin/accounts",
                          headers=basic_auth_user_headers,
                          data=json.dumps(account_data),
                          content_type="application/json")
        assert res.status_code == 401

    def test_create_account_as_admin(self, app, initial_data, client, account_data,  # noqa: F811
                                     basic_auth_admin_headers):  # noqa: F811
        self.client = client
        self.basic_auth_admin_headers = basic_auth_admin_headers

        with app.test_request_context():
            # Create account (as admin)
            res = client.post("/api/v1/pdnsadmin/accounts",
                              headers=basic_auth_admin_headers,
                              data=json.dumps(account_data),
                              content_type="application/json")
            data = res.get_json(force=True)
            assert res.status_code == 201

    def test_update_account_fail(
            self, initial_data, client,  # noqa: F811
            account_data,  # noqa: F811
            basic_auth_user_headers,
            basic_auth_admin_headers):  # noqa: F811
        self.client = client
        self.basic_auth_admin_headers = basic_auth_admin_headers

        # Check account
        data = self.check_account(account_data)
        account_id = data["id"]

        # Update to defaults (should fail)
        res = client.put(
            "/api/v1/pdnsadmin/accounts/{}".format(account_id),
            data=json.dumps(account_data),
            headers=basic_auth_user_headers,
            content_type="application/json",
        )
        assert res.status_code == 401

    def test_delete_account_fail(
            self, initial_data, client,  # noqa: F811
            account_data,  # noqa: F811
            basic_auth_user_headers,
            basic_auth_admin_headers):  # noqa: F811
        self.client = client
        self.basic_auth_admin_headers = basic_auth_admin_headers

        # Check account
        data = self.check_account(account_data)
        account_id = data["id"]

        # Delete account (should fail)
        res = client.delete(
            "/api/v1/pdnsadmin/accounts/{}".format(account_id),
            data=json.dumps(account_data),
            headers=basic_auth_user_headers,
            content_type="application/json",
        )
        assert res.status_code == 401

    def test_delete_account_as_admin(
            self, client, initial_data,  # noqa: F811
            account_data,  # noqa: F811
            basic_auth_admin_headers):  # noqa: F811
        self.client = client
        self.basic_auth_admin_headers = basic_auth_admin_headers

        # Check account
        data = self.check_account(account_data)
        account_id = data["id"]

        # Cleanup (delete account as admin)
        res = client.delete(
            "/api/v1/pdnsadmin/accounts/{}".format(account_id),
            data=json.dumps(account_data),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 204

    def test_users(
            self, client, initial_data,  # noqa: F811
            user1_data,  # noqa: F811
            basic_auth_admin_headers, basic_auth_user_headers):  # noqa: F811
        self.client = client
        self.basic_auth_admin_headers = basic_auth_admin_headers

        # Create user1 (should fail)
        res = client.post(
            "/api/v1/pdnsadmin/users",
            headers=basic_auth_user_headers,
            data=json.dumps(user1_data),
            content_type="application/json",
        )
        assert res.status_code == 401

        # Create user1 (as admin)
        res = client.post(
            "/api/v1/pdnsadmin/users",
            headers=basic_auth_admin_headers,
            data=json.dumps(user1_data),
            content_type="application/json",
        )
        data = res.get_json(force=True)
        assert res.status_code == 201
        assert isinstance(data, dict)
        assert len(data) == 6
        assert data.get('id', None)

        # Check user
        user1 = self.check_user(user1_data, data)
        user1_id = user1["id"]

        # Update to defaults (should fail)
        res = client.put(
            "/api/v1/pdnsadmin/users/{}".format(user1_id),
            data=json.dumps(user1_data),
            headers=basic_auth_user_headers,
            content_type="application/json",
        )
        assert res.status_code == 401

        # Delete user (should fail)
        res = client.delete(
            "/api/v1/pdnsadmin/users/{}".format(user1_id),
            data=json.dumps(user1_data),
            headers=basic_auth_user_headers,
            content_type="application/json",
        )
        assert res.status_code == 401

        # Cleanup (delete user as admin)
        res = client.delete(
            "/api/v1/pdnsadmin/users/{}".format(user1_id),
            data=json.dumps(user1_data),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 204

    def test_account_users(
            self, client, initial_data,  # noqa: F811
            account_data, user1_data,  # noqa: F811
            basic_auth_admin_headers, basic_auth_user_headers):  # noqa: F811
        self.client = client
        self.basic_auth_admin_headers = basic_auth_admin_headers

        # Create account
        res = client.post(
            "/api/v1/pdnsadmin/accounts",
            headers=basic_auth_admin_headers,
            data=json.dumps(account_data),
            content_type="application/json",
        )
        data = res.get_json(force=True)
        assert res.status_code == 201

        # Check account
        data = self.check_account(account_data)
        account_id = data["id"]

        # Create user1
        res = client.post(
            "/api/v1/pdnsadmin/users",
            headers=basic_auth_admin_headers,
            data=json.dumps(user1_data),
            content_type="application/json",
        )
        data = res.get_json(force=True)
        assert res.status_code == 201
        assert isinstance(data, dict)
        assert len(data) == 6
        assert data.get('id', None)

        # Check user
        user1 = self.check_user(user1_data, data)
        user1_id = user1["id"]

        # Assert test account has no users
        res = client.get(
            "/api/v1/pdnsadmin/accounts/users/{}".format(account_id),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        data = res.get_json(force=True)
        assert res.status_code == 200
        assert data == []

        # Link user to account (as user, should fail)
        res = client.put(
            "/api/v1/pdnsadmin/accounts/users/{}/{}".format(
                account_id, user1_id),
            headers=basic_auth_user_headers,
            content_type="application/json",
        )
        assert res.status_code == 401

        # Link user to account (as admin)
        res = client.put(
            "/api/v1/pdnsadmin/accounts/users/{}/{}".format(
                account_id, user1_id),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 204

        # Unlink user from account (as user, should fail)
        res = client.delete(
            "/api/v1/pdnsadmin/accounts/users/{}/{}".format(
                account_id, user1_id),
            headers=basic_auth_user_headers,
            content_type="application/json",
        )
        assert res.status_code == 401

        # Unlink user from account (as admin)
        res = client.delete(
            "/api/v1/pdnsadmin/accounts/users/{}/{}".format(
                account_id, user1_id),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 204

        # Cleanup (delete user)
        res = client.delete(
            "/api/v1/pdnsadmin/users/{}".format(user1_id),
            data=json.dumps(user1_data),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 204

        # Cleanup (delete account)
        res = client.delete(
            "/api/v1/pdnsadmin/accounts/{}".format(account_id),
            data=json.dumps(account_data),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 204
