"""Detect a stored password that is the bcrypt hash of an empty string.

An older user update assigned a missing password as '' and then hashed it.
The account keeps a normal-looking bcrypt hash, and a later sign-in with an
empty password matches that hash.
"""
import bcrypt


def stored_password_is_blank(stored):
    """True when ``stored`` is a bcrypt hash of an empty password."""
    if not isinstance(stored, str) or not stored.startswith(('$2a$', '$2b$', '$2y$')):
        return False
    try:
        return bcrypt.checkpw(b'', stored.encode('ascii'))
    except (ValueError, TypeError):
        return False
