

class IntegrationApiManagement(object):

    def get_account(self, account_name, status_code=200):
        res = self.client.get(
            "/api/v1/pdnsadmin/accounts/{}".format(account_name),
            headers=self.basic_auth_admin_headers,
            content_type="application/json",
        )
        if isinstance(status_code, (tuple, list)):
            assert res.status_code in status_code
        elif status_code:
            assert res.status_code == status_code
        if res.status_code == 200:
            data = res.get_json(force=True)
            assert len(data) == 1
            return data[0]
        return None

    def check_account(self, cmpdata, data=None):
        data = self.get_account(cmpdata["name"])
        for key, value in cmpdata.items():
            assert data[key] == value
        return data

    def get_user(self, username, status_code=200):
        res = self.client.get(
            "/api/v1/pdnsadmin/users/{}".format(username),
            headers=self.basic_auth_admin_headers,
            content_type="application/json",
        )
        if isinstance(status_code, (tuple, list)):
            assert res.status_code in status_code
        elif status_code:
            assert res.status_code == status_code
        assert res.status_code == status_code
        if status_code == 200:
            data = res.get_json(force=True)
            assert len(data) == 1
            return data[0]
        return None

    def check_user(self, cmpdata, data=None):
        if data is None:
            data = self.get_user(cmpdata["username"])
        for key, value in data.items():
            if key in ('username', 'firstname', 'lastname', 'email'):
                assert cmpdata[key] == value
            elif key == 'role':
                assert data[key]['name'] == cmpdata['role_name']
            else:
                assert key in ("id",)
        return data
