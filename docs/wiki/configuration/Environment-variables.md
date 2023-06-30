# Supported environment variables

| Variable                       | Description                                                              | Required   | Default value |
|--------------------------------|--------------------------------------------------------------------------|------------|---------------|
| BIND_ADDRESS                   | 
| CSRF_COOKIE_SECURE             | 
| SESSION_TYPE                   | null                                                                     | filesystem | sqlalchemy    |  | filesystem | 
| LDAP_ENABLED                   | 
| LOCAL_DB_ENABLED               | 
| LOG_LEVEL                      | 
| MAIL_DEBUG                     |
| MAIL_DEFAULT_SENDER            | 
| MAIL_PASSWORD                  | 
| MAIL_PORT                      | 
| MAIL_SERVER                    | 
| MAIL_USERNAME                  | 
| MAIL_USE_SSL                   | 
| MAIL_USE_TLS                   | 
| OFFLINE_MODE                   | 
| OIDC_OAUTH_API_URL             |                                                                          |            |               |
| OIDC_OAUTH_AUTHORIZE_URL       |
| OIDC_OAUTH_TOKEN_URL           |                                                                          |            |               |
| OIDC_OAUTH_METADATA_URL        |                                                                          |            |               |
| PORT                           | 
| SERVER_EXTERNAL_SSL            | Forceful override of URL schema detection when using the url_for method. | False      | None          |
| REMOTE_USER_COOKIES            |
| REMOTE_USER_LOGOUT_URL         |
| SALT                           |
| SAML_ASSERTION_ENCRYPTED       |
| SAML_ATTRIBUTE_ACCOUNT         | 
| SAML_ATTRIBUTE_ADMIN           | 
| SAML_ATTRIBUTE_EMAIL           | 
| SAML_ATTRIBUTE_GIVENNAME       | 
| SAML_ATTRIBUTE_GROUP           | 
| SAML_ATTRIBUTE_NAME            | 
| SAML_ATTRIBUTE_SURNAME         | 
| SAML_ATTRIBUTE_USERNAME        | 
| SAML_CERT                      | 
| SAML_DEBUG                     | 
| SAML_ENABLED                   | 
| SAML_GROUP_ADMIN_NAME          | 
| SAML_GROUP_TO_ACCOUNT_MAPPING  | 
| SAML_IDP_SSO_BINDING           | 
| SAML_IDP_ENTITY_ID             | 
| SAML_KEY                       | 
| SAML_LOGOUT                    | 
| SAML_LOGOUT_URL                | 
| SAML_METADATA_CACHE_LIFETIME   | 
| SAML_METADATA_URL              | 
| SAML_NAMEID_FORMAT             | 
| SAML_PATH                      | 
| SAML_SIGN_REQUEST              | 
| SAML_SP_CONTACT_MAIL           | 
| SAML_SP_CONTACT_NAME           | 
| SAML_SP_ENTITY_ID              | 
| SAML_WANT_MESSAGE_SIGNED       | 
| SECRET_KEY                     | Flask secret key [^1]                                                    | Y          | no default    |
| SESSION_COOKIE_SECURE          | 
| SIGNUP_ENABLED                 | 
| SQLALCHEMY_DATABASE_URI        | SQL Alchemy URI to connect to database                                   | N          | no default    |
| SQLALCHEMY_TRACK_MODIFICATIONS |
| SQLALCHEMY_ENGINE_OPTIONS      | json string. e.g. '{"pool_recycle":600,"echo":1}' [^2]                   |

[^1]: Flask secret key (see https://flask.palletsprojects.com/en/1.1.x/config/#SECRET_KEY for how to generate)
[^2]: See Flask-SQLAlchemy Documentation for all engine options.
