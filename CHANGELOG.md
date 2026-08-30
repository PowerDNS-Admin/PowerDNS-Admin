# Changelog

## [Unreleased]

## [2026.08.1] - 2026-08-30

### Breaking Changes

-   Release identifiers now use Calendar Versioning in the form
    `YYYY.0M.RELEASE`, beginning with `2026.08.1`, instead of Semantic
    Versioning. Git tags retain the `v` prefix, while the application version
    and changelog omit it. Automation or deployment constraints that assume
    `MAJOR.MINOR.PATCH` must be updated for the new scheme.
-   PowerDNS-Admin no longer supplies an implicit SQLite database URI.
    Deployments must now set `SQLALCHEMY_DATABASE_URI`, configure that value in
    a Python configuration file, or provide the required split `DATABASE_*`
    environment variables. Existing standalone Docker deployments that relied
    on the default must explicitly set
    `SQLALCHEMY_DATABASE_URI=sqlite:////data/powerdns-admin.db` to continue
    using their database in the `/data` volume.
-   OIDC provider logout now follows OpenID Connect RP-Initiated Logout 1.0:
    the request uses `post_logout_redirect_uri`, `id_token_hint`, and
    `client_id` instead of the legacy `redirect_uri` parameter. Deployments
    must register the externally visible PowerDNS-Admin `/oidc/logged-out` URL
    as an allowed post-logout redirect URI. Providers that only accept
    proprietary or legacy logout parameters may require a provider-specific
    endpoint or integration.
-   SAML HTTP-Redirect URL encoding no longer defaults to lowercase percent
    escapes. The previous unconditional AD FS compatibility behavior could
    alter the query string used to validate responses from providers such as
    Keycloak, causing otherwise valid signed logout responses to be rejected.
    Deployments whose identity provider requires lowercase percent escapes for
    signed outbound login or logout requests must now explicitly set
    `SAML_LOWERCASE_URLENCODING=true`. Adding this setting allows those AD FS
    deployments to retain their required request encoding without changing
    exact-query signature validation or the provider-neutral default for other
    SAML identity providers.
-   The release version file moved from the repository root `VERSION` to
    `powerdnsadmin/VERSION`. Application startup reads that package path via
    `app.root_path` and fails if the file is missing or empty. Docker images,
    packaging scripts, CI, and bare-metal installs that still expect or inject
    a root-level `VERSION` must ship or generate `powerdnsadmin/VERSION`
    instead. The footer renders that value as `APP_VERSION` at runtime.
-   `SQLALCHEMY_ENGINE_OPTIONS` now defaults to `pool_pre_ping=True` and
    `pool_recycle=600` in both `default_config` and `AppSettings`.
    Deployments that relied on the previous empty/unset engine options
    (unbounded connection reuse, or a custom `SQLALCHEMY_ENGINE_OPTIONS`
    that assumed no built-in pool settings) will see different pooling
    behavior: connections are pinged on checkout and recycled after 600
    seconds. Override `SQLALCHEMY_ENGINE_OPTIONS` explicitly if you need
    different values; setting the variable replaces the entire options
    dict rather than merging with these defaults.

### Features

-   Database connection settings can be supplied as separate `DATABASE_*`
    environment variables (`DRIVER`, `USER`, `PASSWORD`, `HOST`, `PORT`,
    `NAME`, `EXTRA_PARAMS`) instead of a single `SQLALCHEMY_DATABASE_URI`.
    User and password are percent-encoded automatically so Docker Compose can
    share an unencoded password with other services. `DATABASE_EXTRA_PARAMS`
    appends driver-specific URI query flags such as `ssl=true`. An explicit
    `SQLALCHEMY_DATABASE_URI` (or `_FILE`) still wins when set. The development
    and production Docker Compose stacks use the split variables. (`#1899`)
-   The top navbar now hosts an AdminLTE-style user menu card (avatar, name,
    role, profile, and sign out), replacing the previous sidebar user panel.
    The menu uses a resolved display name (first and last name, falling back to
    username) for the toggle label and image `alt` text, and the fullscreen
    control is hidden below the `md` breakpoint so it does not crowd the right
    cluster on small screens.
-   When no LDAP photo or Gravatar is available, `/user/image` now serves a
    generated initials avatar (stable color per username) and falls back to a
    circle-user SVG instead of the old silhouette PNG.
-   Global Search moves into a centered navbar control (placeholder plus
    search icon) that submits to the existing global search page, so it stays
    available without a sidebar entry. `/` or `Ctrl`/`Cmd+K` still focus the
    field, a clear control overlays the input when a query is present without
    changing the field width, and on smaller viewports the search icon expands
    the field in the bar instead of navigating away (the icon still links to
    Global Search without JavaScript).
-   The development Docker Compose environment defaults to an OpenLDAP identity
    source built from Alpine packages of the OpenLDAP Project software, with
    seeded bind accounts, role users, and groups mapped to the Administrator,
    Operator, and User roles. FreeIPA remains available through
    `docker/docker-compose-dev.freeipa.yml`.
-   The development PowerDNS-Admin authenticates those users directly over LDAP,
    while Keycloak 26.7 federates the same directory for OpenID Connect and
    SAML, including attribute and group-to-role mappings.
-   The development stack now uses a persistent MySQL 8.4 database for
    PowerDNS-Admin (schema created and seeded automatically). Keycloak shares
    that server on an isolated schema and accepts both HTTP and HTTPS callbacks
    for local proxy testing.
-   The development Docker environment now sets `PDNS_API_URL` so
    PowerDNS-Admin is preconfigured for the composed PowerDNS API and no longer
    prompts for the API URL on first login.
-   The development Terraform PowerDNS seeder now stores state in the staged
    PostgreSQL service (`pg` backend, `terraform` database) instead of a local
    state file or named volume. Provider plugins are downloaded on each seeder
    run. This is for net-new deployments only; existing local-state volumes are
    not migrated.

### Testing

-   Unit, smoke, and Compose Python tests now use MySQL 8.4 for the application
    database and SQLAlchemy sessions (same credentials as the development
    stack). The SQLite test-config default is removed; CI unit/smoke jobs start
    a MySQL 8.4 service container.
-   Added a fast HTTP smoke suite under `tests/smoke/` covering healthcheck,
    `/ping`, `/api`, `/swagger`, login page rendering, local login/logout,
    anonymous redirects away from protected pages, admin/operator page loads
    after the template reorganization, dashboard v2 domains JSON without a
    PowerDNS refresh, and footer/`powerdnsadmin/VERSION` consistency. CI runs
    unit tests on the oldest and newest supported Pythons (3.12 and 3.14), runs
    smoke once on Python 3.13, and can also target the suite through the Docker
    Python test Compose stack.
-   Frontend migration tests now cover the split layout includes, navbar Global
    Search control (keyboard focus, clear button, and mobile expand), settings
    child active-page markers, and avatar helper behavior.

### Code Refactoring

-   Authenticated chrome is split out of `base.html` into
    `includes/navbar.html`, `includes/sidebar.html`, and
    `includes/default_modals.html` while keeping the existing pageheader and
    defaultmodals override blocks.
-   The sidebar now highlights individual Settings children, shows the
    Administration section only when Activity and/or admin/operator items apply,
    and uses a distinct icon for Server Configuration versus Settings.
-   OAuth/OIDC and SAML endpoints now use dedicated blueprints registered
    during application setup instead of sharing the main index route module.
    Common post-authentication session handling and federated-identity account
    and role provisioning have been extracted into shared modules, with audit
    history identifying whether provisioning originated from OIDC or SAML.

### Documentation

-   The development guide documents the default OpenLDAP identity backend, the
    optional FreeIPA override, seeded credentials and roles, Keycloak
    administration, SAML metadata endpoints, and the LDAP, OpenID Connect, and
    SAML sign-in flows.
-   The testing guide now documents how to run the smoke suite through Docker
    Compose.
-   Microsoft identity settings, login text, logs, and OAuth documentation now
    use the current Microsoft Entra ID product name. Existing `azure_oauth_*`
    settings and `/azure/` callback routes remain unchanged for compatibility.

### Security

-   Added `.github/secret_scanning.yml` to close Secret Scanning push-protection
    alerts for intentional lab credentials in the dev/test Docker Compose
    stacks, with a callout that `docker/common/postgres-init.sql` and
    `docker/common/mysql-init.sql` are shared by those non-production stacks
    only and must never be reused to initialize a production database.
-   CodeQL's push/pull_request trigger and analysis scope
    (`.github/codeql/codeql-config.yml`) are now kept in sync as a single
    allowlist covering `powerdnsadmin/`, `configs/`, `migrations/`, and the
    top-level entry-point scripts, so scheduled and push/PR scans cover the
    same real application source.


### Bug Fixes

-   The OIDC token-update callback now accepts the additional token context
    supplied by Authlib and safely merges partial refresh responses with the
    existing session token, preserving refresh and access tokens when an
    identity provider omits them from its response. (`#1889`)
-   The `/healthcheck` endpoint no longer marks the visitor session as
    non-permanent or sets the application-wide permanent session lifetime to
    zero, which could cause unrelated authenticated sessions to expire.
    (`#1905`)
-   The navbar Global Search control now uses theme CSS variables so the field
    remains readable in dark mode, and the header uses a responsive grid so the
    centered search no longer overlaps the user menu when the window narrows.
-   The sidebar brand and top navbar now share the same header height, and the
    sidebar uses a 1px right border instead of a box shadow so the four chrome
    corners meet on one pixel.
-   HTTP and SAML error pages now use a standalone AdminLTE 4-style full-page
    layout (Bootstrap utilities, no app sidebar/chrome) instead of the legacy
    in-shell `.error-page` markup.
-   OIDC logout now discovers the provider's `end_session_endpoint`, retains
    the configured logout URL as a fallback, identifies the provider session
    with the login ID token, and delegates redirect construction plus logout
    state generation and validation to Authlib. It reliably clears the local
    session when the provider does not support RP-initiated logout.
-   Logout now removes OAuth callback state, SAML identity and session data,
    pending TOTP and first-login state, and other authentication-only session
    values while retaining unrelated state such as the CSRF token.
-   The development Compose environment now enables SAML single logout so the
    application logout route initiates logout at the Keycloak identity provider.
-   SAML HTTP-Redirect logout signatures are now verified against the exact
    encoded query string received from the identity provider, preventing valid
    Keycloak LogoutResponse signatures from failing after URL re-encoding.
-   SAML, OAuth, and OIDC JIT provisioning now log whether the local user was
    created or already existed together with the resulting role and account
    memberships, and report local user creation or profile-update failures
    instead of continuing with only a successful-authentication message.
-   Users created through SAML, OAuth, or OIDC JIT provisioning now generate a
    `Created user` entry in the application admin history attributed to the
    originating identity provider.
-   Stale OAuth/OIDC callbacks that fail Authlib state validation
    (`MismatchingStateError`) now clear the session and return the login page
    with an expiry message, matching the existing handling for expired login
    and registration CSRF tokens, instead of raising a 500.
-   The development Keycloak SAML client no longer inherits the default
    `role_list` scope (which emitted one `Role` Attribute per realm role) and
    maps groups as a single multi-valued `groups` attribute, so python3-saml's
    strict duplicate-Name check accepts the assertion.
-   Renaming an account no longer raises an `AttributeError` when the edit form
    looks up the account after the name change.
-   The admin history view now loads the correct
    `admin/history/history.html` template path.
-   The PowerDNS API documentation link in settings now points to the current
    upstream URL.
-   The application footer version string is now rendered from
    `powerdnsadmin/VERSION` at runtime for both Docker and bare-metal
    deployments, instead of a hard-coded template value.

## [0.6.1] - 2026-08-06

### Features

-   The default local production Docker Compose stack now builds PowerDNS-Admin from the checked-out source and starts a persistent MySQL 8.4 service, waiting for the database to become healthy before running migrations and starting the application.

### Documentation

-   The Docker installation and build guides now distinguish the standalone Docker Hub image's SQLite default from the repository Compose stack's bundled MySQL database and document the current `docker compose` build workflow.

### Bug Fixes

-   Empty password values submitted when users edit their own profile or when administrators edit a user are now treated as no password change instead of being hashed.
-   OpenID Connect authentication now automatically adds the required `openid` scope while preserving configured scopes, fixing sign-in failures with providers such as Microsoft Entra ID when existing settings omit it.
-   OpenID Connect authentication now combines validated ID-token claims with the UserInfo response, allowing providers such as Microsoft Entra ID to supply `preferred_username` through the ID token when their UserInfo endpoint omits it.
-   Google, GitHub, and Microsoft OAuth callback routes are now registered during application setup, preventing Flask from rejecting late route registration after the first request.

## [0.6.0] - 2026-08-05

### Breaking Changes

-   This release removes support for PowerDNS versions older than 5.0. Users running older versions of PowerDNS will need to use an older version of PowerDNS-Admin.
-   The minimum supported Python version is now 3.12; Python 3.10 and 3.11 are no longer supported.

### Features

-   A new GitHub Actions workflow to automatically add support information to release notes.
-   A new GitHub Actions test workflow runs unit tests on the minimum and maximum supported Python versions and the complete Docker-based Python suite, retaining Compose logs when failures occur.
-   New structured bug, feature, and documentation issue forms and an expanded pull-request template collect reproduction details, testing evidence, compatibility impact, security impact, screenshots, and changelog information.
-   A new `app-support.json` file to consolidate the supported versions of Python, browsers, and the PowerDNS Authoritative Server.
-   A new guide for migrating from SQLite to MySQL or PostgreSQL.
-   A new `docs/RELEASE_TEMPLATE.md` documenting the release notes format (Highlights + categorized changelog) and the steps for cutting a release.

### Documentation

-   The `README.md`, `docs/running_tests.md`, and `docs/wiki/debug/build-process.md` have been updated for consistency, clarity, and tone.
-   The README now links to the development test workflow, uses current Docker Compose and Flask documentation, and replaces hard-coded branch URLs with relative repository links.
-   Contributor and release documentation now describe the active `dev` branch workflow, expected pull-request evidence, and the supported-version release-note process.
-   Outdated and historical documentation has been removed.
-   `README.md` gained a Compatibility section stating the PowerDNS version support policy: built and tested against the current stable release plus recent prior minor releases, with support for anything older than 5.0 dropped entirely regardless of PowerDNS's own upstream backport policy.

### Code Refactoring

-   All backward compatibility checks for older versions of PowerDNS have been removed from the codebase.
-   The `pdns_version` setting has been removed from the application.
-   Regular-expression literals now use raw strings, invalid escape sequences are rejected during CI, and the removed standard-library `distutils.strtobool` helper has been replaced with an internal boolean parser.
-   Unified DNS record formatting through the shared zone/template record helper: TXT values are emitted with one set of outer quotes, APL input is trimmed, and HTTPS/SVCB target names and simple quoted service parameters are normalized before being placed in the editor.

### Bug Fixes

-   PowerDNS zone names are now URL-encoded consistently in zone, record, and API-management request paths, preventing failures for names containing characters that require escaping.
-   Zone synchronization now updates catalog membership for existing zones when PowerDNS reports a changed or removed catalog.
-   The OIDC authorization callback is now registered with the application blueprint at startup, preventing Flask 3 from raising an `AssertionError` after request handling has begun.
-   The Docker image's entrypoint and scenario scripts are now installed with world-execute permission (`chmod 0755`) instead of owner-only (`chmod u+x`), fixing a startup failure when the container is run as a non-root user (`docker run --user`, or Kubernetes `runAsNonRoot`/Pod Security Standards).

### Security

-   OIDC access-denied callback parameters are now rendered through the escaped 400 error template instead of being returned as raw text, preventing reflected cross-site scripting.

### Performance

-   Added schema-managed composite indexes for API permission checks, API-key domain/account associations, and per-domain setting lookups, with an Alembic migration for existing SQLite, MySQL, and PostgreSQL installations.
-   Dashboard v2 now reuses its total zone count when no search filter is active, eliminating a redundant database count query for administrators, operators, and regular users.
-   Regular users no longer trigger a global PowerDNS zone synchronization when loading the classic or v2 dashboard; foreground synchronization and the v2 initial-refresh request are now limited to administrators and operators.

### Project Maintenance

-   Modernized the CodeQL, image-publishing, MegaLinter, release-note, stale-thread, and lock-thread workflows with current Actions, explicit permissions, concurrency controls, job timeouts, and `dev`/`master` branch targeting.
-   Made release-note supported-version updates idempotent so rerunning the release workflow replaces its generated block instead of duplicating it.
-   Expanded Dependabot to cover npm, pip, GitHub Actions, and Docker on a grouped weekly schedule, with optional CVE-specific labeling through a narrowly scoped GitHub App.
-   Changed stale automation to retain inactive issues, exempt assigned and milestone work, remove stale labels when activity resumes, and use neutral contributor-facing messages.
-   Separated the Python test suite from the seeded browser-test deployment and added an explicit Chrome/light smoke mode while retaining the full Chrome, Edge, and Firefox light/dark matrix by default.
-   Added Docker-native Python branch coverage reporting with terminal, XML, and HTML output under `docker/test-results/coverage`, plus an optional `COVERAGE_FAIL_UNDER` threshold for local and CI enforcement.
-   Removed the obsolete LGTM configuration now superseded by CodeQL.

### Supported Versions

-   Python: 3.12, 3.13, 3.14
-   Browsers: Chrome 150+, Edge 150+, Firefox 151+
-   PowerDNS Authoritative Server: 5.0, 5.1

## [0.5.1] - 2026-08-02

### Supported Versions

-   Python: 3.10, 3.11, 3.12, 3.13
-   Browsers: Chrome 150+, Edge 150+, Firefox 151+
-   PowerDNS Authoritative Server: 4.9, 5.0, 5.1

### Highlights

-   Modernized the frontend with AdminLTE 4, Bootstrap 5, and a new dark/light/auto theme toggle.
-   Added an optional Dashboard v2 experience with paginated, searchable, server-rendered zone lists.
-   Strengthened account security with TOTP-based two-factor authentication and replay protection.
-   Expanded DNSSEC management with key rollover tracking and live registrar DS-record propagation checks (Beta).
-   Expanded zone functionality with catalog zones and the APL, HTTPS, and SVCB record types.
-   Closed sixteen authorization, session, and information-disclosure gaps across the API and login flow. See [Security](#security) below; upgrading is recommended for all deployments, especially those exposing the API.

### Added

-   Dashboard v2: a new client-rendered zone dashboard with paginated, server-side domain loading, forward/reverse (IPv4/IPv6) zone tabs, a search/rows-per-page toolbar, and a table footer, available alongside the classic dashboard via a new "Preview dashboard v2" link.
-   DNSSEC key rollover tracking with stable public-key fingerprints, cancellation safeguards, and live registrar DS-record propagation checks against parent authoritative nameservers. Dashboard v2 also lets admins choose the key type (CSK/KSK/ZSK), algorithm, and size when enabling DNSSEC, instead of relying on an implicit backend default.
-   TOTP-based two-factor authentication login flow, prompting for an OTP token only when the account has TOTP configured. Password and OTP entry are now two distinct steps (the password isn't re-submitted alongside the token), and `?restart=1` cancels a pending OTP challenge and starts over.
-   TOTP replay protection: OTP tokens can no longer be reused once accepted, while still tolerating roughly one time-step of clock drift.
-   Catalog zone support (#1607): producer/consumer zone relationships, a "Catalog Membership" control for assigning a zone to a catalog, and a "Catalog Member Zones" listing on the catalog zone itself.
-   Opt-in support for the APL, HTTPS, and SVCB DNS record types.
-   Dark / light / auto color-mode toggle, persisted across sessions.
-   `/healthcheck` route used by container health checks.
-   A reusable dual-list ("shuttle") widget for assigning users/zones/accounts in the admin account, API key, and zone-settings screens, replacing the old jQuery UI multiSelect/quicksearch plugins.
-   `POWERDNSADMIN_ASSETS_PREBUILT` environment variable to disable Flask-Assets auto-building, for container images that ship prebuilt frontend bundles without the Node/Yarn toolchain.
-   `SESSION_CLEANUP_N_REQUESTS` setting (default 100) controlling how often the session reaper runs.
-   Terraform-based PowerDNS dataset seeder for generating large deterministic zone/record sets in the dev environment.
-   Browser automation test suite (Chrome, Edge, Firefox; light and dark mode) for console-error auditing.
-   Independent Docker Compose environments for development, Python tests, browser tests, and dependency auditing.
-   Expanded unit and integration test coverage for Dashboard v2, DNSSEC flows, catalog zones, TOTP/session behavior, and new record types.

### Changed

-   Migrated the frontend to AdminLTE 4 and Bootstrap 5, including shared breadcrumbs and page headers, Bootstrap 5 modal/tab APIs, a shared record helper for the zone/template editors, and a persistent unsaved-changes banner.
-   Redesigned Dashboard v2 row actions and DNSSEC status: a dedicated "Edit records" button plus a kebab menu (Zone Settings, Manage DNSSEC, Create Template, Zone Changelog, Remove Zone), DNSSEC shown as a plain Signed/Unsigned badge, and dropdown menus now portal to `document.body` so they aren't clipped by responsive table containers (the classic Dashboard's row menu was updated the same way).
-   Replaced the old jQuery Bootstrap Validator plugin with native Bootstrap 5 form validation (`needs-validation`/`was-validated`) across login, registration, and the zone/template/account/PowerDNS-settings forms.
-   Added a small shared frontend JS layer: common DataTable defaults, a Bootstrap 5 modal helper (`showModal`/`showErrorModal`/`showSuccessModal`), and a `formatUtcDateTimeLocal()` helper that replaces moment.js for changelog/history timestamps.
-   Accessibility pass across icon-only controls (sidebar toggle, fullscreen toggle, theme toggle, per-row action buttons) with `aria-label`s, an `aria-live` region for the unsaved-changes banner, keyboard focus handling for "Review Changes", and `prefers-reduced-motion` support for banner/scroll animations.
-   Upgraded the backend to Flask 3, SQLAlchemy 2-style APIs, Werkzeug, Flask-Migrate, and Flask-SeaSurf.
-   Upgraded the Docker base image to Python 3.13 and Yarn 4; updated the PowerDNS test schema for PowerDNS 5.
-   Switched the development and test Docker Compose stacks from SQLite to MySQL/PostgreSQL (the application's own standalone-install default remains SQLite, though its default path moved to `/data/powerdns-admin.db` and is now overridable via a `SQLALCHEMY_DATABASE_URI` environment variable).
-   Reduced the multi-stage development Docker image from approximately 2.1 GB to 456 MB.
-   Reorganized Docker assets under `docker/{common,dev,test,browser-test,production,legacy}/`.
-   Changed the `history.domain_id` foreign key to `ON DELETE SET NULL` so history records survive domain deletion.
-   Moved `pytest` out of `requirements.txt` into a new `requirements-dev.txt`.
-   Moved GitHub Actions runners from `debian-latest` to `ubuntu-latest` and updated the MegaLinter configuration.

### Fixed

-   The session reaper now actually expires stale sessions, invoked from each blueprint's `before_request` hook.
-   The "Remember Me" checkbox on the login form was missing a `name` attribute, so it never submitted.
-   Corrected the Azure authentication documentation for the Scope field.
-   Local user registration's username/email uniqueness checks (`create_local_user()`) were comparing a SQLAlchemy column object rather than a query predicate, so the "already in use" check never actually matched an existing user; duplicate usernames and emails could be registered. Also fixed a crash when no email was supplied.
-   A race between two concurrent local-user registrations could raise an unhandled `IntegrityError`; it's now caught and reported as a normal registration failure.
-   Deleting a zone via the API no longer risks a foreign-key `IntegrityError` on the resulting history entry: `api_login_delete_zone` no longer attaches a `domain_id` for a zone that was just removed locally.
-   `GET /api/v1/pdnsadmin/apikeys` (and the "own keys" listing) no longer returns duplicate rows for a domain reachable through more than one account/domain-user relationship.
-   Unhandled 404s inside `/api/v1/...` now return JSON instead of falling through to Flask's default HTML error page.
-   Disabling DNSSEC on a zone now surfaces the actual backend error (HTTP 502) and correctly updates the domain's DNSSEC/rectify state on failure, instead of always reporting success and leaving stale state when a key deletion failed.
-   Custom record-edit permission settings saved before a new record type (e.g. APL, HTTPS, SVCB) existed no longer silently omit that type; `Setting.get()` now merges stored values over the current defaults.
-   The CAA/MX/SRV/SOA/TLSA/TXT record-helper modal no longer immediately reopens itself after being closed (it previously triggered on field focus, and Bootstrap returns focus to the field once the modal closes).
-   Editing a zone record no longer stacks a duplicate "leave without saving" listener onto every navigation link each time a record is edited.
-   The login page no longer forcibly reloads itself, discarding any in-progress input, every `session_timeout` minutes via a `META REFRESH` tag.
-   Row-action dropdown menus in the dashboard, template, and admin user/key/account tables no longer share one duplicate `id` across every row, which meant every menu was mislabeled for accessibility and could misassociate with the wrong row.
-   The user profile page now returns to the previously active tab after the full-page reload triggered by enabling/disabling 2FA (it previously called Bootstrap's `.tab('show')` immediately before reloading, which had no visible effect).

### Removed

-   Legacy frontend dependencies: iCheck, FastClick, Moment, jQuery UI, SlimScroll, Sparkline, Multiselect, Quicksearch, and Bootstrap Validator.
-   Legacy SQLite Docker assets for the development/test stacks.

### Security

-   TOTP tokens are now single-use, preventing an intercepted or observed code from being replayed to authenticate again.
-   Fixed an API authentication confusion bug where a Basic Auth request made alongside an existing browser session was authorized using the session's identity instead of the credentials actually supplied for that request.
-   The zone-deletion API endpoint is now gated by the zone-removal permission instead of the zone-creation permission, so a user allowed to create zones can no longer delete zones when removal is disabled.
-   Operators can no longer create or promote an API key to the Administrator role.
-   Centralized user role-change authorization (no self-role-change; only Administrators/Operators may change roles; only Administrators may modify or promote to Administrator) and applied it consistently to both the admin UI and the user-management API, closing a gap where the API did not enforce the self-role-change restriction the UI already had.
-   The `/api/v1/servers` PowerDNS-forwarding endpoints now require an Administrator-role API key, instead of accepting any valid key regardless of scope.
-   `/api/v1/sync_domains` now requires an Administrator or Operator, instead of any authenticated API caller.
-   Closed an ID-existence oracle in the API key lookup endpoint so a non-owner receives the same response whether a key ID belongs to another user or does not exist at all.
-   Narrowed the user API-key listing endpoint to keys actually scoped to the caller's own accessible domains, excluding broader account- or admin/operator-scoped keys reachable via a shared domain join.
-   Expired CSRF submissions on the login and registration forms now force a session clear before re-rendering, so a rejected stale submission cannot leave a partially authenticated session behind.
-   The server-side session is now regenerated immediately after a successful login, closing a session-fixation window where a session ID issued before authentication could be reused afterward; the authenticated session also gets its own fresh expiry instead of inheriting one from a long-open login page.
-   An Operator-role API credential can no longer create a new user with the Administrator role, promote an existing user to Administrator, or modify any field of an existing Administrator account via `/api/v1/pdnsadmin/users`; only an Administrator may do either. (This is separate from the API-key promotion restriction above — this one covers user accounts.)
-   API responses no longer serialize an API key's bcrypt hash: `ApiKeySchema` dropped its `key` field, so only the one-time key-creation response can expose key material.
-   New API keys are no longer written to the application log in bcrypt-hashed form at creation time.
-   The profile-image endpoint no longer serves an uploaded image with an undefined content-type when its signature isn't recognized; unrecognized uploads now get an explicit `application/octet-stream` fallback instead of a browser-sniffable one.
