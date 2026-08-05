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
(Highlights + categorized sections), plus the same two closing sections
GitHub's own auto-generated release notes have always used for this repo
(see any pre-0.5.1 release, e.g. v0.4.2) — match that convention exactly
rather than inventing a new one:

```markdown
# vX.Y.Z

<Highlights + categorized sections, copied from CHANGELOG.md>

### New Contributors

* <name or @handle> made their first contribution in <full PR URL, bare, no markdown link>

**Full Changelog**: https://github.com/PowerDNS-Admin/PowerDNS-Admin/compare/vPREV...vX.Y.Z
```

**New Contributors** only lists people with zero commits reachable from the
previous tag (`git log --author=<email> --oneline vPREV | wc -l` == 0) —
check each contributor, don't assume. Omit the section entirely if no one
qualifies. There is no separate aggregate "Contributors" list — GitHub's
native format doesn't have one (attribution normally lives in a per-PR
"What's Changed" list, which this project's Highlights+categorized format
replaces, so don't add a substitute for it).

GitHub's own "auto-generate release notes" feature computes New
Contributors and the compare link automatically, but only when drafting a
release against a tag that doesn't have a release yet — it cannot be
invoked to backfill an already-published release. When updating an
existing/legacy release's notes (as opposed to cutting a new one), there
is no automation to lean on: run the `git log` check above by hand for
every contributor and write the section yourself.

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
