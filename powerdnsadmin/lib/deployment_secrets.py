import os

import bcrypt

# Secret keys shipped in this repository. A process still using one of them
# can mint email-confirmation links, and previously could mint remember-me
# cookies, for any account.
MIN_SECRET_KEY_LENGTH = 32
PUBLISHED_SECRET_KEYS = frozenset({
    'e951e5a1f4b94151b360f47edf596dd2',
    'changeme_secret',
    'a-very-secret-key',
    'NotVerySecret',
    'INSECURE-CHANGE-ME-9I0DAtfkfj5JmBkPSaHah3ECAa8Df5KK',
})
# Every bcrypt salt assigned in this repository's published history.
PUBLISHED_SALTS = frozenset({
    '$2b$12$yLUMTIfl21FKJQpTkRQXCu',
})


def _allow_insecure_secrets(app):
    if app.config.get('TESTING'):
        return True
    flag = os.environ.get('PDA_ALLOW_INSECURE_SECRETS', '')
    return flag.lower() in {'1', 'true', 'yes', 'on'}


def _secret_key_rejected(secret):
    if not isinstance(secret, str):
        return True
    # A secrets file from ``echo key > secret`` keeps a trailing newline.
    # Length and the published-key list have to see the value operators set.
    stripped = secret.strip()
    if stripped == '' or len(stripped) < MIN_SECRET_KEY_LENGTH:
        return True
    return stripped in PUBLISHED_SECRET_KEYS


def _salt_rejected(salt):
    if not isinstance(salt, str) or len(salt) != 29:
        return True
    try:
        encoded = salt.encode('ascii')
        cost = encoded[4:6]
        if not cost.isdigit() or not 4 <= int(cost) <= 31:
            return True
        # Let bcrypt validate the version and salt bytes. Probe at minimum
        # cost so even a valid cost of 31 cannot stall startup validation.
        # The configured salt and its cost remain unchanged for API keys.
        bcrypt.hashpw(b'check', encoded[:4] + b'04' + encoded[6:])
    except (ValueError, UnicodeEncodeError):
        return True
    return False


def _warn_published_salt(app, salt):
    if not isinstance(salt, str) or salt.strip() not in PUBLISHED_SALTS:
        return
    app.logger.warning(
        'SALT matches a salt published in the PowerDNS-Admin repository.'
    )


def assert_deployment_secrets(app):
    """Stop startup when the signing key or the API-key salt is unusable.

    Tests and local experiments set TESTING or PDA_ALLOW_INSECURE_SECRETS=1.
    SECRET_KEY must be at least 32 characters and must not be a published
    default. SALT must be a bcrypt salt (``$2b$12$`` plus 22 salt characters).
    A salt published in this repository logs a warning and startup continues.
    """
    if _allow_insecure_secrets(app):
        return

    salt = app.config.get('SALT')
    _warn_published_salt(app, salt)

    problems = []
    if _secret_key_rejected(app.config.get('SECRET_KEY')):
        problems.append('SECRET_KEY')
    if _salt_rejected(salt):
        problems.append('SALT')
    if not problems:
        return

    raise RuntimeError(
        'Refusing to start because {0} is missing, too short, malformed, or '
        'still a published PowerDNS-Admin default. Set a new SECRET_KEY of '
        'at least {1} characters. SALT must be a bcrypt salt. See the '
        'environment variables documentation. SECRET_KEY signs '
        'email-confirmation links and the session cookie. SALT is the '
        'bcrypt salt for API keys.'.format(
            ' and '.join(problems), MIN_SECRET_KEY_LENGTH)
    )
