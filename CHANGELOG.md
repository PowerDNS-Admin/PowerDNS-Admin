# Changelog

## [0.5.1]

Summary of changes since `v0.4.2`.

### Added

- Dashboard v2: a new client-rendered zone dashboard with paginated,
  server-side domain loading, forward/reverse (IPv4/IPv6) zone tabs, a
  search/rows-per-page toolbar, and a table footer, available alongside the
  classic dashboard.
- DNSSEC key rollover tracking with stable public-key fingerprints,
  cancellation safeguards, and live registrar DS-record propagation checks
  against parent authoritative nameservers.
- TOTP-based two-factor authentication login flow, prompting for an OTP
  token only when the account has TOTP configured.
- TOTP replay protection: OTP tokens can no longer be reused once accepted,
  while still tolerating roughly one time-step of clock drift.
- Catalog zone support (#1607).
- Opt-in support for the APL, HTTPS, and SVCB DNS record types.
- Dark / light / auto color-mode toggle, persisted across sessions.
- `/healthcheck` route used by container health checks.
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
  they aren't clipped by responsive table containers.
- Upgraded the backend to Flask 3, SQLAlchemy 2-style APIs, Werkzeug,
  Flask-Migrate, and Flask-SeaSurf; bumped Flask-Session from 0.4.0 to
  0.6.0.
- Upgraded the Docker base image to Python 3.13 and Yarn 4; updated the
  PowerDNS test schema for PowerDNS 5.
- Switched the development and test Docker Compose stacks from SQLite to
  MySQL/PostgreSQL (the application's own standalone-install default
  remains SQLite).
- Reduced the multi-stage development Docker image from approximately
  2.1 GB to 456 MB.
- Reorganized Docker assets under `docker/{common,dev,test,browser-test,
  production,legacy}/`.
- Changed the `history.domain_id` foreign key to `ON DELETE SET NULL` so
  history records survive domain deletion.
- Moved GitHub Actions runners from `debian-latest` to `ubuntu-latest` and
  updated the MegaLinter configuration.

### Fixed

- The session reaper now actually expires stale sessions, invoked from each
  blueprint's `before_request` hook.
- The "Remember Me" checkbox on the login form (was missing a `name`
  attribute, so it never submitted).
- Corrected the Azure authentication documentation for the Scope field.

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
