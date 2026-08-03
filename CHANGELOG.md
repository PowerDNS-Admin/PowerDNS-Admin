# Changelog

## [Unreleased]

### Breaking Changes

-   This release removes support for PowerDNS versions older than 5.0. Users running older versions of PowerDNS will need to use an older version of PowerDNS-Admin.

### Features

-   A new GitHub Actions workflow to automatically add support information to release notes.
-   A new `app-support.json` file to consolidate the supported versions of Python, browsers, and the PowerDNS Authoritative Server.
-   A new guide for migrating from SQLite to PostgreSQL or MySQL.
-   A new `docs/RELEASE_TEMPLATE.md` documenting the release notes format (Highlights + categorized changelog) and the steps for cutting a release.

### Documentation

-   The `README.md`, `docs/running_tests.md`, and `docs/wiki/debug/build-process.md` have been updated for consistency, clarity, and tone.
-   Outdated and historical documentation has been removed.
-   `README.md` gained a Compatibility section stating the PowerDNS version support policy: built and tested against the current stable release plus recent prior minor releases, with support for anything older than 5.0 dropped entirely regardless of PowerDNS's own upstream backport policy.

### Code Refactoring

-   All backward compatibility checks for older versions of PowerDNS have been removed from the codebase.
-   The `pdns_version` setting has been removed from the application.

### Supported Versions

-   Python: 3.10, 3.11, 3.12, 3.13, 3.14
-   Browsers: Chrome 150+, Edge 150+, Firefox 151+
-   PowerDNS Authoritative Server: 5.0, 5.1

## [0.5.1] - 2026-08-02

### Supported Versions

- Python: 3.10, 3.11, 3.12, 3.13
- Browsers: Chrome 150+, Edge 150+, Firefox 151+
- PowerDNS Authoritative Server: 4.9, 5.0, 5.1

### Highlights

This release focuses on three areas: a modernized frontend, stronger
account security, and expanded DNS/zone functionality. The UI has been
rebuilt on AdminLTE 4 and Bootstrap 5 with a new dark/light/auto theme
toggle, and zones now have an optional Dashboard v2 experience with
paginated, searchable, server-rendered zone lists. Account security gains
TOTP-based two-factor authentication with replay protection, and DNSSEC
management gains key rollover tracking with live registrar DS-record
propagation checks (Beta). Zone functionality expands to cover catalog zones and
the APL, HTTPS, and SVCB record types. Alongside these, a dedicated
security pass closed sixteen separate authorization, session, and
information-disclosure gaps across the API and login flow (see
[Security](#security) below) — upgrading is recommended for all
deployments, especially those exposing the API.

### Added

- Dashboard v2: a new client-rendered zone dashboard with paginated,
  server-side domain loading, forward/reverse (IPv4/IPv6) zone tabs, a
  search/rows-per-page toolbar, and a table footer, available alongside the
  classic dashboard via a new "Preview dashboard v2" link.
- DNSSEC key rollover tracking with stable public-key fingerprints,
  cancellation safeguards, and live registrar DS-record propagation checks
  against parent authoritative nameservers. Dashboard v2 also lets admins
  choose the key type (CSK/KSK/ZSK), algorithm, and size when enabling
  DNSSEC, instead of relying on an implicit backend default.
- TOTP-based two-factor authentication login flow, prompting for an OTP
  token only when the account has TOTP configured. Password and OTP entry
  are now two distinct steps (the password isn't re-submitted alongside the
  token), and `?restart=1` cancels a pending OTP challenge and starts over.
- TOTP replay protection: OTP tokens can no longer be reused once accepted,
  while still tolerating roughly one time-step of clock drift.
- Catalog zone support (#1607): producer/consumer zone relationships, a
  "Catalog Membership" control for assigning a zone to a catalog, and a
  "Catalog Member Zones" listing on the catalog zone itself.
- Opt-in support for the APL, HTTPS, and SVCB DNS record types.
- Dark / light / auto color-mode toggle, persisted across sessions.
- `/healthcheck` route used by container health checks.
- A reusable dual-list ("shuttle") widget for assigning users/zones/accounts
  in the admin account, API key, and zone-settings screens, replacing the
  old jQuery UI multiSelect/quicksearch plugins.
- `POWERDNSADMIN_ASSETS_PREBUILT` environment variable to disable
  Flask-Assets auto-building, for container images that ship prebuilt
  frontend bundles without the Node/Yarn toolchain.
- `SESSION_CLEANUP_N_REQUESTS` setting (default 100) controlling how often
  the session reaper runs.
- Terraform-based PowerDNS dataset seeder for generating large deterministic
  zone/record sets in the dev environment.
- Browser automation test suite (Chrome, Edge, Firefox; light and dark mode)
  for console-error auditing.
- Independent Docker Compose environments for development, Python tests,
  browser tests, and dependency auditing.
- Expanded unit and integration test coverage for Dashboard v2, DNSSEC
  flows, catalog zones, TOTP/session behavior, and new record types.

### Changed

- Migrated the frontend to AdminLTE 4 and Bootstrap 5, including shared
  breadcrumbs and page headers, Bootstrap 5 modal/tab APIs, a shared record
  helper for the zone/template editors, and a persistent unsaved-changes
  banner.
- Redesigned Dashboard v2 row actions and DNSSEC status: a dedicated "Edit
  records" button plus a kebab menu (Zone Settings, Manage DNSSEC, Create
  Template, Zone Changelog, Remove Zone), DNSSEC shown as a plain
  Signed/Unsigned badge, and dropdown menus now portal to `document.body` so
  they aren't clipped by responsive table containers (the classic
  Dashboard's row menu was updated the same way).
- Replaced the old jQuery Bootstrap Validator plugin with native Bootstrap 5
  form validation (`needs-validation`/`was-validated`) across login,
  registration, and the zone/template/account/PowerDNS-settings forms.
- Added a small shared frontend JS layer: common DataTable defaults, a
  Bootstrap 5 modal helper (`showModal`/`showErrorModal`/`showSuccessModal`),
  and a `formatUtcDateTimeLocal()` helper that replaces moment.js for
  changelog/history timestamps.
- Accessibility pass across icon-only controls (sidebar toggle, fullscreen
  toggle, theme toggle, per-row action buttons) with `aria-label`s, an
  `aria-live` region for the unsaved-changes banner, keyboard focus handling
  for "Review Changes", and `prefers-reduced-motion` support for banner/scroll
  animations.
- Upgraded the backend to Flask 3, SQLAlchemy 2-style APIs, Werkzeug,
  Flask-Migrate, and Flask-SeaSurf
- Upgraded the Docker base image to Python 3.13 and Yarn 4; updated the
  PowerDNS test schema for PowerDNS 5.
- Switched the development and test Docker Compose stacks from SQLite to
  MySQL/PostgreSQL (the application's own standalone-install default
  remains SQLite, though its default path moved to
  `/data/powerdns-admin.db` and is now overridable via a
  `SQLALCHEMY_DATABASE_URI` environment variable).
- Reduced the multi-stage development Docker image from approximately
  2.1 GB to 456 MB.
- Reorganized Docker assets under `docker/{common,dev,test,browser-test,
  production,legacy}/`.
- Changed the `history.domain_id` foreign key to `ON DELETE SET NULL` so
  history records survive domain deletion.
- Moved `pytest` out of `requirements.txt` into a new `requirements-dev.txt`.
- Moved GitHub Actions runners from `debian-latest` to `ubuntu-latest` and
  updated the MegaLinter configuration.

### Fixed

- The session reaper now actually expires stale sessions, invoked from each
  blueprint's `before_request` hook.
- The "Remember Me" checkbox on the login form (was missing a `name`
  attribute, so it never submitted).
- Corrected the Azure authentication documentation for the Scope field.
- Local user registration's username/email uniqueness checks
  (`create_local_user()`) were comparing a SQLAlchemy column object rather
  than a query predicate, so the "already in use" check never actually
  matched an existing user; duplicate usernames and emails could be
  registered. Also fixed a crash when no email was supplied.
- A race between two concurrent local-user registrations could raise an
  unhandled `IntegrityError`; it's now caught and reported as a normal
  registration failure.
- Deleting a zone via the API no longer risks a foreign-key `IntegrityError`
  on the resulting history entry: `api_login_delete_zone` no longer attaches
  a `domain_id` for a zone that was just removed locally.
- `GET /api/v1/pdnsadmin/apikeys` (and the "own keys" listing) no longer
  returns duplicate rows for a domain reachable through more than one
  account/domain-user relationship.
- Unhandled 404s inside `/api/v1/...` now return JSON instead of falling
  through to Flask's default HTML error page.
- Disabling DNSSEC on a zone now surfaces the actual backend error (HTTP
  502) and correctly updates the domain's DNSSEC/rectify state on failure,
  instead of always reporting success and leaving stale state when a key
  deletion failed.
- Custom record-edit permission settings saved before a new record type
  (e.g. APL, HTTPS, SVCB) existed no longer silently omit that type;
  `Setting.get()` now merges stored values over the current defaults.
- The CAA/MX/SRV/SOA/TLSA/TXT record-helper modal no longer immediately
  reopens itself after being closed (it previously triggered on field
  focus, and Bootstrap returns focus to the field once the modal closes).
- Editing a zone record no longer stacks a duplicate "leave without saving"
  listener onto every navigation link each time a record is edited.
- The login page no longer forcibly reloads itself, discarding any
  in-progress input, every `session_timeout` minutes via a `META REFRESH`
  tag.
- Row-action dropdown menus in the dashboard, template, and admin
  user/key/account tables no longer share one duplicate `id` across every
  row, which meant every menu was mislabeled for accessibility and could
  misassociate with the wrong row.
- The user profile page now returns to the previously active tab after the
  full-page reload triggered by enabling/disabling 2FA (it previously
  called Bootstrap's `.tab('show')` immediately before reloading, which had
  no visible effect).

### Removed

- Legacy frontend dependencies: iCheck, FastClick, Moment, jQuery UI,
  SlimScroll, Sparkline, Multiselect, Quicksearch, and Bootstrap Validator.
- Legacy SQLite Docker assets for the development/test stacks.

### Security

- TOTP tokens are now single-use, preventing an intercepted or observed
  code from being replayed to authenticate again.
- Fixed an API authentication confusion bug where a Basic Auth request made
  alongside an existing browser session was authorized using the session's
  identity instead of the credentials actually supplied for that request.
- The zone-deletion API endpoint is now gated by the zone-removal
  permission instead of the zone-creation permission, so a user allowed to
  create zones can no longer delete zones when removal is disabled.
- Operators can no longer create or promote an API key to the
  Administrator role.
- Centralized user role-change authorization (no self-role-change; only
  Administrators/Operators may change roles; only Administrators may
  modify or promote to Administrator) and applied it consistently to both
  the admin UI and the user-management API, closing a gap where the API
  did not enforce the self-role-change restriction the UI already had.
- The `/api/v1/servers` PowerDNS-forwarding endpoints now require an
  Administrator-role API key, instead of accepting any valid key regardless
  of scope.
- `/api/v1/sync_domains` now requires an Administrator or Operator, instead
  of any authenticated API caller.
- Closed an ID-existence oracle in the API key lookup endpoint so a
  non-owner receives the same response whether a key ID belongs to another
  user or does not exist at all.
- Narrowed the user API-key listing endpoint to keys actually scoped to the
  caller's own accessible domains, excluding broader account- or
  admin/operator-scoped keys reachable via a shared domain join.
- Expired CSRF submissions on the login and registration forms now force a
  session clear before re-rendering, so a rejected stale submission cannot
  leave a partially authenticated session behind.
- The server-side session is now regenerated immediately after a successful
  login, closing a session-fixation window where a session ID issued before
  authentication could be reused afterward; the authenticated session also
  gets its own fresh expiry instead of inheriting one from a long-open login
  page.
- An Operator-role API credential can no longer create a new user with the
  Administrator role, promote an existing user to Administrator, or modify
  any field of an existing Administrator account via
  `/api/v1/pdnsadmin/users`; only an Administrator may do either. (This is
  separate from the API-key promotion restriction above — this one covers
  user accounts.)
- API responses no longer serialize an API key's bcrypt hash: `ApiKeySchema`
  dropped its `key` field, so only the one-time key-creation response can
  expose key material.
- New API keys are no longer written to the application log in
  bcrypt-hashed form at creation time.
- Zone names are now URL-encoded before being spliced into PowerDNS API
  request paths, across all zone-management call sites.
- The profile-image endpoint no longer serves an uploaded image with an
  undefined content-type when its signature isn't recognized; unrecognized
  uploads now get an explicit `application/octet-stream` fallback instead
  of a browser-sniffable one.