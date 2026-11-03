import bcrypt

from powerdnsadmin.lib.blank_password import stored_password_is_blank


def test_bcrypt_hash_of_empty_password_is_blank():
    stored = bcrypt.hashpw(b'', bcrypt.gensalt()).decode('ascii')

    assert stored_password_is_blank(stored)


def test_bcrypt_hash_of_a_password_is_not_blank():
    stored = bcrypt.hashpw(b'secret-password', bcrypt.gensalt()).decode('ascii')

    assert not stored_password_is_blank(stored)


def test_non_bcrypt_values_are_not_blank():
    assert not stored_password_is_blank(None)
    assert not stored_password_is_blank('')
    assert not stored_password_is_blank('*')
    assert not stored_password_is_blank('$2b$12$not-a-valid-salt')
