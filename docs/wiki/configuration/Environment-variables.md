# Environment Variables

The following environment variables are supported for configuring the application.

`PDNS_API_URL` and `PDNS_API_KEY` can also be supplied through a Python
configuration file or Docker secrets (`PDNS_API_URL_FILE` / `PDNS_API_KEY_FILE`).
For each setting, an explicit environment or secret-file value takes precedence
over the Python configuration, and deployment configuration takes precedence over
the database. These settings appear read-only in **Settings > Server**, with the
source shown. Update the deployment and restart the application to change them.
An explicitly empty value is also deployment-owned and must be fixed there.

If a setting is omitted from deployment configuration, administrators can edit it
in-app and save it in the database. The URL and key are managed independently, so
one can be deployment-owned while the other remains editable. Existing database
values are preserved beneath deployment overrides; removing an override and
restarting restores the saved value (or the empty default when none is saved).

| Variable                       | Description                                                              | Required   | Default Value |
|--------------------------------|--------------------------------------------------------------------------|------------|---------------|
| BIND_ADDRESS                   |                                                                          |            |               |
| CSRF_COOKIE_SECURE             |                                                                          |            |               |
| SESSION_TYPE                   |                                                                          |            | `sqlalchemy`  |
| LDAP_ENABLED                   |                                                                          |            |               |
| LOCAL_DB_ENABLED               |                                                                          |            |               |
| LOG_LEVEL                      |                                                                          |            |               |
| MAIL_DEBUG                     |                                                                          |            |               |
| MAIL_DEFAULT_SENDER            |                                                                          |            |               |
| MAIL_PASSWORD                  |                                                                          |            |               |
| MAIL_PORT                      |                                                                          |            |               |
| MAIL_SERVER                    |                                                                          |            |               |
| MAIL_USERNAME                  |                                                                          |            |               |
| MAIL_USE_SSL                   |                                                                          |            |               |
| MAIL_USE_TLS                   |                                                                          |            |               |
| OFFLINE_MODE                   |                                                                          |            |               |
| OIDC_OAUTH_API_URL             |                                                                          |            |               |
| OIDC_OAUTH_AUTHORIZE_URL       |                                                                          |            |               |
| OIDC_OAUTH_TOKEN_URL           |                                                                          |            |               |
| OIDC_OAUTH_METADATA_URL        |                                                                          |            |               |
| PORT                           |                                                                          |            |               |
| SERVER_EXTERNAL_SSL            | Forcefully overrides URL schema detection when using the `url_for` method. | No         | `None`        |
| REMOTE_USER_COOKIES            |                                                                          |            |               |
| REMOTE_USER_LOGOUT_URL         |                                                                          |            |               |
| SALT                           | Salt for API-key hashing and email-confirmation tokens. Validated by bcrypt at startup; a missing or unusable value is refused. The published salt is accepted with a warning. Replacing it invalidates existing API keys and outstanding email-confirmation links. [^1] | No | Shipped value |
| SAML_ASSERTION_ENCRYPTED       |                                                                          |            |               |
| SAML_ATTRIBUTE_ACCOUNT         |                                                                          |            |               |
| SAML_ATTRIBUTE_ADMIN           |                                                                          |            |               |
| SAML_ATTRIBUTE_EMAIL           |                                                                          |            |               |
| SAML_ATTRIBUTE_GIVENNAME       |                                                                          |            |               |
| SAML_ATTRIBUTE_GROUP           |                                                                          |            |               |
| SAML_ATTRIBUTE_NAME            |                                                                          |            |               |
| SAML_ATTRIBUTE_SURNAME         |                                                                          |            |               |
| SAML_ATTRIBUTE_USERNAME        |                                                                          |            |               |
| SAML_CERT                      |                                                                          |            |               |
| SAML_DEBUG                     |                                                                          |            |               |
| SAML_ENABLED                   |                                                                          |            |               |
| SAML_GROUP_ADMIN_NAME          |                                                                          |            |               |
| SAML_GROUP_TO_ACCOUNT_MAPPING  |                                                                          |            |               |
| SAML_IDP_SSO_BINDING           |                                                                          |            |               |
| SAML_IDP_ENTITY_ID             |                                                                          |            |               |
| SAML_KEY                       |                                                                          |            |               |
| SAML_LOGOUT                    |                                                                          |            |               |
| SAML_LOGOUT_URL                |                                                                          |            |               |
| SAML_LOWERCASE_URLENCODING     | Use lowercase percent escapes for outbound SAML HTTP-Redirect requests for AD FS compatibility. | No | `false` |
| SAML_METADATA_CACHE_LIFETIME   |                                                                          |            |               |
| SAML_METADATA_URL              |                                                                          |            |               |
| SAML_NAMEID_FORMAT             |                                                                          |            |               |
| SAML_PATH                      |                                                                          |            |               |
| SAML_SIGN_REQUEST              |                                                                          |            |               |
| SAML_SP_CONTACT_MAIL           |                                                                          |            |               |
| SAML_SP_CONTACT_NAME           |                                                                          |            |               |
| SAML_SP_ENTITY_ID              |                                                                          |            |               |
| SAML_WANT_MESSAGE_SIGNED       |                                                                          |            |               |
| SECRET_KEY                     | Signs email-confirmation links and the session cookie. At least 32 characters. The built-in value is refused at startup. [^1] | Yes | Built-in value refused |
| SESSION_COOKIE_SECURE          |                                                                          |            |               |
| SIGNUP_ENABLED                 |                                                                          |            |               |
| SQLALCHEMY_DATABASE_URI        | SQL Alchemy URI to connect to the database. Takes precedence over `DATABASE_*`. | Yes, unless using `DATABASE_*` | No default |
| DATABASE_DRIVER                | Driver used to build the URI: `mysql`, `mariadb`, `postgres`/`postgresql`, or `sqlite`. | No | `mysql` |
| DATABASE_USER                  | Database username. Percent-encoded when the URI is built.                | No         |               |
| DATABASE_PASSWORD              | Database password. Percent-encoded when the URI is built.                | No         |               |
| DATABASE_HOST                  | Database hostname or IP. Required for MySQL/PostgreSQL when using `DATABASE_*`. | No | |
| DATABASE_PORT                  | Database port. Omitted from the URI when unset.                          | No         |               |
| DATABASE_NAME                  | Database name, or SQLite file path. Required when using `DATABASE_*`.    | No         |               |
| DATABASE_EXTRA_PARAMS          | Extra URI query flags, e.g. `ssl=true&charset=utf8mb4`. Values must already be URL-encoded. | No | |
| SQLALCHEMY_TRACK_MODIFICATIONS |                                                                          |            |               |
| SQLALCHEMY_ENGINE_OPTIONS      | A JSON string, e.g., `'{"pool_pre_ping":true,"pool_recycle":600}'` [^2]   |            | `{"pool_pre_ping": true, "pool_recycle": 600}` |

PowerDNS-Admin has no default database URI. Set `SQLALCHEMY_DATABASE_URI`, configure it in a Python configuration file, or provide the required `DATABASE_*` variables. When `SQLALCHEMY_DATABASE_URI` is unset, PowerDNS-Admin builds it from the `DATABASE_*` variables. That avoids a second, URL-encoded copy of the password in Compose files when the value contains `@`, `#`, commas, or other reserved characters. Driver-specific URI flags (TLS, charset, timeouts, and similar) go in `DATABASE_EXTRA_PARAMS` as a query string. The query string is appended unchanged apart from an optional leading `?`, so its values must already be URL-encoded. Docker-style secrets work on these names too (for example `DATABASE_PASSWORD_FILE=/run/secrets/db_password`).

[^1]: Generate `SECRET_KEY` with `python3 -c 'import secrets; print(secrets.token_hex(32))'`. For a new deployment, generate `SALT` with `python3 -c 'import bcrypt; print(bcrypt.gensalt().decode())'`. Keep these values stable across restarts. `SECRET_KEY_FILE` and `SALT_FILE` are read the same way as other Docker secrets, and a trailing newline is removed. A bcrypt salt contains `$`. In a Compose file, pass it through the environment instead of writing the `$` characters directly.

    `SALT` must be a 29-character ASCII bcrypt salt with a cost from 04 through 31 and salt characters accepted by bcrypt. Generate it with `bcrypt.gensalt()` rather than writing one by hand. For example, `$2b$12$UniqueDeploySaltValue1` looks like a salt but bcrypt rejects it; costs such as `00` and `99` are also invalid. Startup rejects these values before they can break API-key creation or authentication. Validation does not change the configured salt or the cost used to hash API keys; higher costs make API-key creation and authentication more expensive.

    `SALT` is not a secret. It is used for API-key hashing and as the signing context for email-confirmation tokens. Token forgery still requires `SECRET_KEY`, which must remain private. An existing deployment may retain its valid published salt; this logs a warning and does not require API-key rotation. Replacing `SALT` invalidates every existing API key and outstanding email-confirmation link. User passwords use independently generated bcrypt salts.

[^2]: For a list of all available engine options, please see the Flask-SQLAlchemy documentation.
