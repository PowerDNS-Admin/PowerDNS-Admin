import os
import re

# Values shipped in this repository. A process still using one of them can
# mint email-confirmation links, and previously could mint remember-me
# cookies, for any account.
MIN_SECRET_KEY_LENGTH = 32
_BCRYPT_SALT = re.compile(r'^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{22}$')
PUBLISHED_SECRET_KEYS = frozenset({
    'e951e5a1f4b94151b360f47edf596dd2',
    'changeme_secret',
    'a-very-secret-key',
    'NotVerySecret',
    'INSECURE-CHANGE-ME-9I0DAtfkfj5JmBkPSaHah3ECAa8Df5KK',
})
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
    stripped = secret.strip()
    if stripped == '' or len(secret) < MIN_SECRET_KEY_LENGTH:
        return True
    return secret in PUBLISHED_SECRET_KEYS


def _salt_rejected(salt):
    if not isinstance(salt, str) or _BCRYPT_SALT.match(salt) is None:
        return True
    return salt in PUBLISHED_SALTS


def assert_deployment_secrets(app):
    """Stop startup when signing keys are missing, weak, or published.

    Tests and local experiments set TESTING or PDA_ALLOW_INSECURE_SECRETS=1.
    SECRET_KEY must be at least 32 characters. SALT must be a bcrypt salt
    (``$2b$12$`` plus 22 salt characters) because API keys are hashed with it.
    """
    if _allow_insecure_secrets(app):
        return

    problems = []
    if _secret_key_rejected(app.config.get('SECRET_KEY')):
        problems.append('SECRET_KEY')
    if _salt_rejected(app.config.get('SALT')):
        problems.append('SALT')
    if not problems:
        return

    raise RuntimeError(
        'Refusing to start because {0} is missing, too short, malformed, or '
        'still a published PowerDNS-Admin default. Set a new random '
        'SECRET_KEY of at least {1} characters and a bcrypt SALT before '
        'starting. SECRET_KEY signs email-confirmation links and the session '
        'cookie. SALT is the bcrypt salt for API keys, so replacing it makes '
        'every existing API key stop working. Tests set TESTING or '
        'PDA_ALLOW_INSECURE_SECRETS=1.'.format(
            ' and '.join(problems), MIN_SECRET_KEY_LENGTH)
    )
