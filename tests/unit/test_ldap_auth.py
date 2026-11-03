import ldap
import ldap.filter

from powerdnsadmin.models.setting import Setting
from powerdnsadmin.models.user import User


LDAP_SETTINGS = {
    'ldap_type': 'ldap',
    'ldap_base_dn': 'dc=example,dc=com',
    'ldap_filter_basic': '(objectClass=person)',
    'ldap_filter_username': 'uid',
    'ldap_filter_group': '(objectClass=groupOfNames)',
    'ldap_filter_groupname': 'member',
    'ldap_admin_group': 'cn=admins,dc=example,dc=com',
    'ldap_operator_group': '',
    'ldap_user_group': 'cn=users,dc=example,dc=com',
    'ldap_sg_enabled': True,
    'ldap_domain': 'example.com',
}


def ldap_settings(monkeypatch, **overrides):
    settings = dict(LDAP_SETTINGS)
    settings.update(overrides)
    monkeypatch.setattr(
        Setting, 'get', lambda self, name: settings.get(name))


def entry(username):
    return [[(
        'uid={0},dc=example,dc=com'.format(username),
        {'uid': [username.encode('utf-8')]},
    )]]


def test_ldap_user_filter_keeps_filter_characters_inside_the_value():
    username = "admin)(|(uid=*"
    user = User(username=username, reload_info=False)

    search_filter = user.ldap_user_filter('uid', '(objectClass=person)')

    assert search_filter == "(&(uid={0})(objectClass=person))".format(
        ldap.filter.escape_filter_chars(username))
    assert 'uid=*' not in search_filter
    assert ')(|(' not in search_filter


def test_ldap_connection_uses_the_authentication_lease_as_its_timeout(
        app, monkeypatch):
    options = {}

    class Connection:
        def set_option(self, option, value):
            options[option] = value

    monkeypatch.setattr(ldap, 'initialize', lambda uri: Connection())
    monkeypatch.setattr(ldap, 'set_option', lambda *args: None)
    monkeypatch.setattr(Setting, 'get', lambda self, name: 'ldap://example')
    monkeypatch.setitem(app.config, 'AUTH_LDAP_TIMEOUT', 7)

    with app.app_context():
        User(username='alice', reload_info=False).ldap_init_conn()

    assert options[ldap.OPT_TIMEOUT] == 7.0
    assert options[ldap.OPT_NETWORK_TIMEOUT] == 7.0


def test_ldap_operations_share_one_authentication_deadline(app, monkeypatch):
    import time as time_module

    from powerdnsadmin.lib.auth_throttle import PasswordAttempt

    clock = {'now': 100.0}
    monkeypatch.setattr(time_module, 'monotonic', lambda: clock['now'])
    monkeypatch.setitem(app.config, 'AUTH_IN_FLIGHT_LEASE', 30)
    waits = []
    searched = {'n': 0}

    class Connection:
        def set_option(self, option, value):
            return None

        def simple_bind(self, who, cred):
            return 1

        def result(self, msgid, all=1, timeout=None):
            waits.append(timeout)
            clock['now'] += 20
            return ldap.RES_BIND, []

        def search(self, *args, **kwargs):
            searched['n'] += 1
            return 2

        def whoami_s(self):
            return 'dn:uid=alice,dc=example,dc=com'

    monkeypatch.setattr(ldap, 'initialize', lambda uri: Connection())
    monkeypatch.setattr(ldap, 'set_option', lambda *args: None)
    settings = {
        'ldap_uri': 'ldap://example',
        'ldap_type': 'ldap',
        'ldap_admin_username': 'cn=admin',
        'ldap_admin_password': 'secret',
    }
    monkeypatch.setattr(Setting, 'get', lambda self, name: settings.get(name))
    user = User(username='alice', password='secret', reload_info=False)

    with app.app_context():
        with PasswordAttempt('alice', 'secret', False, '198.51.100.200'):
            assert user.ldap_auth(
                'uid=alice,dc=example,dc=com', 'secret') is True
            user.ldap_search('(uid=alice)', 'dc=example,dc=com')

    assert waits[0] == 30
    assert waits[1] == 10
    assert searched['n'] == 0


def test_ldap_auth_rejects_empty_password_without_binding(app, monkeypatch):
    user = User(username='alice', password='', reload_info=False)

    def connect(self):
        raise AssertionError('empty password must not open an LDAP connection')

    monkeypatch.setattr(User, 'ldap_init_conn', connect)

    with app.app_context():
        assert user.ldap_auth('uid=alice,dc=example,dc=com', '') is False
        assert user.ldap_auth('uid=alice,dc=example,dc=com', None) is False


def test_anonymous_ldap_bind_is_not_a_user():
    class AnonymousBind:
        def whoami_s(self):
            return 'dn:'

    user = User(username='alice', reload_info=False)
    assert user._ldap_bind_identified_user(AnonymousBind()) is False


def test_injected_username_cannot_take_another_entrys_role(
        app, monkeypatch):
    username = '*)(uid=*'
    user = User(
        username=username,
        password='not-the-admin-password',
        plain_text_password='not-the-admin-password',
        reload_info=False,
    )
    ldap_settings(monkeypatch)
    captured = {}

    def search(self, search_filter, base_dn, retrieve_attributes=None):
        captured['filter'] = search_filter
        return entry('ttodd-adm')

    def bind(self, bind_dn, password):
        raise AssertionError('must not bind as the unmatched directory entry')

    def change_role(self, role_name):
        raise AssertionError('must not copy a role from another account')

    monkeypatch.setattr(User, 'ldap_search', search)
    monkeypatch.setattr(User, 'ldap_auth', bind)
    monkeypatch.setattr(User, 'set_role', change_role)

    with app.app_context():
        assert user.is_validate('LDAP', src_ip='109.94.96.109') is False

    assert captured['filter'] == user.ldap_user_filter(
        'uid', '(objectClass=person)')


def test_empty_password_cannot_inherit_a_matching_admins_role(
        app, monkeypatch):
    user = User(
        username='rr-preg10xB0402',
        password='',
        plain_text_password='',
        reload_info=False,
    )
    ldap_settings(monkeypatch)

    def search(self, search_filter, base_dn, retrieve_attributes=None):
        if 'cn=admins' in base_dn:
            return entry('admins')
        return entry('rr-preg10xB0402')

    def change_role(self, role_name):
        raise AssertionError('empty password must not change the role')

    monkeypatch.setattr(User, 'ldap_search', search)
    monkeypatch.setattr(User, 'set_role', change_role)

    with app.app_context():
        assert user.is_validate('LDAP', src_ip='109.94.96.109') is False
