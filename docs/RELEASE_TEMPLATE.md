# Release Notes Format

This document defines how PowerDNS-Admin writes release notes, for both
`CHANGELOG.md` and the GitHub Release page. Follow it when cutting a new
release so notes stay consistent without needing to be reinvented each time.

## Source of truth: CHANGELOG.md

`CHANGELOG.md` follows [Keep a Changelog](https://keepachangelog.com/).
Contributors add entries under `## [Unreleased]` as they merge PRs, grouped
into:

- **Breaking Changes** — anything requiring action before/during upgrade.
- **Added** — new features.
- **Changed** — behavior changes to existing features.
- **Fixed** — bug fixes.
- **Removed** — deleted features, dependencies, or files.
- **Security** — vulnerability fixes or authorization/permission hardening.
- **Deprecated** — features slated for removal (when applicable).
- **Supported Versions** — added at release-cut time only (see below), not
  accumulated in `Unreleased`.

Omit any category with nothing to report. Each bullet should be specific
enough that a reader can tell exactly what changed without reading the
diff: name the affected route/file/setting, state the old and new
behavior, and reference an issue/PR number (`#1234`) when one exists.
Prefer "The zone-deletion API endpoint is now gated by the zone-removal
permission" over "Fixed a permission bug."

## Cutting a release

1. Rename `## [Unreleased]` to `## [x.y.z] - YYYY-MM-DD`.
2. Add a **Highlights** subsection directly under the version header,
   before **Breaking Changes**/**Added**/etc. (see below).
3. Add a **Supported Versions** subsection as the last section of the
   dated entry, pulling straight from the current `app-support.json`:
   ```markdown
   ### Supported Versions

   - Python: <python.supported_versions>
   - Browsers: <browsers, "name minimum_version+", comma-separated>
   - PowerDNS Authoritative Server: <powerdns_auth.supported_versions>
   ```
4. Start a fresh empty `## [Unreleased]` section above it.
5. Tag and publish the release. The `release-notes.yml` workflow
   independently appends the same three lists to the GitHub Release
   body — this is redundant with step 3 by design (CHANGELOG.md should
   fully document the release on its own; the workflow just saves
   re-typing it into the GitHub Release). Don't hand-author the GitHub
   Release's copy — let CI append it — but do write the CHANGELOG.md
   copy by hand at cut time.

## Highlights section

3–6 sentences of prose, written for someone deciding whether to upgrade —
not a bullet restatement of the changelog. Cover:

- What the release is *about* (1 sentence framing the theme(s)).
- The 2–4 changes a typical operator most needs to know, in plain
  language.
- Whether upgrading is urgent (security fixes, breaking changes) or
  routine, and any explicit call-out if action is required before
  upgrading.

Skip internal/dev-only changes here (CI, Docker dev images, test
tooling) even if they're substantial in the full changelog — Highlights
is for what changes for someone running the app.

## GitHub Release body

The GitHub Release body is the CHANGELOG.md entry for that version
(Highlights + categorized sections), plus two additions that don't belong
in CHANGELOG.md itself:

```markdown
# vX.Y.Z

<Highlights + categorized sections, copied from CHANGELOG.md>

## Contributors

<@handle1, @handle2, ... — from `git shortlog -sne vPREV..vX.Y.Z`>

**Full Changelog**: https://github.com/PowerDNS-Admin/PowerDNS-Admin/compare/vPREV...vX.Y.Z
```

The supported-versions block is appended after publish by CI; leave it out
of what you draft by hand.

## Style notes

- Wrap prose at a reasonable width; match the existing CHANGELOG.md
  formatting (bullets wrapped, not one giant line).
- Use backticks for file paths, routes, settings, and identifiers.
- Reference issues/PRs (`#1234`) inline where they add traceability,
  not on every bullet.
- Don't editorialize ("massive", "huge win") — state what changed and let
  the reader judge significance from the Highlights framing.
