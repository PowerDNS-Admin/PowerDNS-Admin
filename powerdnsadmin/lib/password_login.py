"""Rules shared by the login form, browser Basic auth, and API Basic auth.

API keys are a separate credential and do not pass through here. A user
password presented anywhere else has to satisfy the same account policy as
the login form. When the account has a TOTP secret, the one-time code is
read from the ``X-OTP`` header because Basic authentication has no second
field of its own.
"""


def password_login_blocked(user, method, local_db_enabled, verify_user_email):
    """Return a user-facing reason to stop, or ``None`` when the password may be checked.

    ``local_db_enabled`` is only treated as off when it is explicitly false.
    A missing setting keeps the historical default, which is local login on.
    """
    if method == 'LOCAL' and local_db_enabled is False:
        return 'Local authentication is disabled'
    if (verify_user_email and getattr(user, 'email', None)
            and not user.confirmed):
        return 'Please confirm your email address first'
    return None


def otp_login_blocked(user, otp_token):
    """Return a reason when this account requires a one-time code that was not accepted."""
    if not getattr(user, 'otp_secret', None):
        return None
    token = '' if otp_token is None else str(otp_token).strip()
    if not token.isdigit() or not user.verify_totp(token):
        return 'Multi-factor authentication required'
    return None
