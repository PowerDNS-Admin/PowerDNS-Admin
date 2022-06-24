import json

from . import IntegrationApiManagement


class TestIntegrationApiManagementAdminUser(IntegrationApiManagement):

    def test_accounts_empty_get(
            self, client, initial_data,                         # noqa: F811
            basic_auth_admin_headers):                          # noqa: F811
        res = client.get("/api/v1/pdnsadmin/accounts",
                         headers=basic_auth_admin_headers)
        data = res.get_json(force=True)
        assert res.status_code == 200
        assert data == []

    def test_users_empty_get(
            self, client, initial_data,                         # noqa: F811
            test_admin_user, test_user,                         # noqa: F811
            basic_auth_admin_headers):                          # noqa: F811
        res = client.get("/api/v1/pdnsadmin/users",
                         headers=basic_auth_admin_headers)
        data = res.get_json(force=True)
        assert res.status_code == 200
        # Initally contains 2 records
        assert len(data) == 2
        for user in data:
            assert user["username"] in (test_admin_user, test_user)

    def test_accounts(
            self, client, initial_data,                         # noqa: F811
            account_data,                                       # noqa: F811
            basic_auth_admin_headers):                          # noqa: F811
        account_name = account_data["name"]
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

        updated = account_data.copy()
        # Update and check values
        for upd_key in ["description", "contact", "mail"]:
            upd_value = "upd-{}".format(account_data[upd_key])

            # Update
            data = {"name": account_name, upd_key: upd_value}
            res = client.put(
                "/api/v1/pdnsadmin/accounts/{}".format(account_id),
                data=json.dumps(data),
                headers=basic_auth_admin_headers,
                content_type="application/json",
            )
            assert res.status_code == 204
            updated[upd_key] = upd_value

            # Check
            data = self.check_account(updated)

        # Update to defaults
        res = client.put(
            "/api/v1/pdnsadmin/accounts/{}".format(account_id),
            data=json.dumps(account_data),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 204

        # Check account
        res = client.get(
            "/api/v1/pdnsadmin/accounts/{}".format(account_name),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        data = res.get_json(force=True)
        assert res.status_code == 200
        assert isinstance(data, dict)
        assert len(data) == 7
        assert data.get('id', None)
        account_id = data["id"]
        for key, value in account_data.items():
            assert data[key] == value

        # Cleanup (delete account)
        res = client.delete(
            "/api/v1/pdnsadmin/accounts/{}".format(account_id),
            data=json.dumps(account_data),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 204

        # Get non-existing account (should fail)
        data = self.get_account(account_name, status_code=404)

        # Update non-existing account (should fail)
        res = client.put(
            "/api/v1/pdnsadmin/accounts/{}".format(account_id),
            data=json.dumps(account_data),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 404

        # Delete non-existing account (should fail)
        res = client.delete(
            "/api/v1/pdnsadmin/accounts/{}".format(account_id),
            data=json.dumps(account_data),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 404

    def test_users(
            self, client, initial_data,                         # noqa: F811
            user1_data,                                         # noqa: F811
            basic_auth_admin_headers):                          # noqa: F811
        user1name = user1_data["username"]
        self.client = client
        self.basic_auth_admin_headers = basic_auth_admin_headers

        # Create user (user1)
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

        updated = user1_data.copy()
        # Update and check values
        for upd_key in ["firstname", "lastname", "email"]:
            upd_value = "upd-{}".format(user1_data[upd_key])

            # Update
            data = {"username": user1name, upd_key: upd_value}
            res = client.put(
                "/api/v1/pdnsadmin/users/{}".format(user1_id),
                data=json.dumps(data),
                headers=basic_auth_admin_headers,
                content_type="application/json",
            )
            assert res.status_code == 204
            updated[upd_key] = upd_value

            # Check
            data = self.check_user(updated)

        # Update to defaults
        res = client.put(
            "/api/v1/pdnsadmin/users/{}".format(user1_id),
            data=json.dumps(user1_data),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 204

        # Check user
        self.check_user(user1_data)

        # Cleanup (delete user)
        res = client.delete(
            "/api/v1/pdnsadmin/users/{}".format(user1_id),
            data=json.dumps(user1_data),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 204

        # Get non-existing user (should fail)
        data = self.get_user(user1name, status_code=404)

        # Update non-existing user (should fail)
        res = client.put(
            "/api/v1/pdnsadmin/users/{}".format(user1_id),
            data=json.dumps(user1_data),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 404

        # Delete non-existing user (should fail)
        res = client.delete(
            "/api/v1/pdnsadmin/users/{}".format(user1_id),
            data=json.dumps(user1_data),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 404

    def test_account_users(
            self, client, initial_data,                         # noqa: F811
            test_user, account_data, user1_data,                # noqa: F811
            basic_auth_admin_headers):                          # noqa: F811
        self.client = client
        self.basic_auth_admin_headers = basic_auth_admin_headers
        test_user_id = self.get_user(test_user)["id"]

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

        # Assert unlinking an unlinked account fails
        res = client.delete(
            "/api/v1/pdnsadmin/accounts/users/{}/{}".format(
                account_id, user1_id),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 404

        # Link user to account
        res = client.put(
            "/api/v1/pdnsadmin/accounts/users/{}/{}".format(
                account_id, user1_id),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 204

        # Check user is linked to account
        res = client.get(
            "/api/v1/pdnsadmin/accounts/users/{}".format(account_id),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        data = res.get_json(force=True)
        assert res.status_code == 200
        assert len(data) == 1
        self.check_user(user1_data, data[0])

        # Unlink user from account
        res = client.delete(
            "/api/v1/pdnsadmin/accounts/users/{}/{}".format(
                account_id, user1_id),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 204

        # Check user is unlinked from account
        res = client.get(
            "/api/v1/pdnsadmin/accounts/users/{}".format(account_id),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        data = res.get_json(force=True)
        assert res.status_code == 200
        assert data == []

        # Unlink unlinked user from account (should fail)
        res = client.delete(
            "/api/v1/pdnsadmin/accounts/users/{}/{}".format(
                account_id, user1_id),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 404

        # Cleanup (delete user)
        res = client.delete(
            "/api/v1/pdnsadmin/users/{}".format(user1_id),
            data=json.dumps(user1_data),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 204

        # Link non-existing user to account (should fail)
        res = client.put(
            "/api/v1/pdnsadmin/accounts/users/{}/{}".format(
                account_id, user1_id),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 404

        # Unlink non-exiting user from account (should fail)
        res = client.delete(
            "/api/v1/pdnsadmin/accounts/users/{}/{}".format(
                account_id, user1_id),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 404

        # Cleanup (delete account)
        res = client.delete(
            "/api/v1/pdnsadmin/accounts/{}".format(account_id),
            data=json.dumps(account_data),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 204

        # List users in non-existing account (should fail)
        res = client.get(
            "/api/v1/pdnsadmin/accounts/users/{}".format(account_id),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 404

        # Link existing user to non-existing account (should fail)
        res = client.put(
            "/api/v1/pdnsadmin/accounts/users/{}/{}".format(
                account_id, test_user_id),
            headers=basic_auth_admin_headers,
            content_type="application/json",
        )
        assert res.status_code == 404
