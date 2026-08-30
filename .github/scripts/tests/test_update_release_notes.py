import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / 'update-release-notes.py'
)
SPEC = importlib.util.spec_from_file_location('update_release_notes', SCRIPT_PATH)
release_notes = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = release_notes
SPEC.loader.exec_module(release_notes)


SUPPORT = {
    'python': {'supported_versions': ['3.12', '3.13']},
    'browsers': {
        'chrome': {'minimum_version': '150'},
        'firefox': {'minimum_version': '151'},
    },
    'powerdns_auth': {'supported_versions': ['5.0', '5.1']},
}

CHANGELOG = """# Changelog

## [Unreleased]

## [2026.08.1] - 2026-08-30

### Highlights

The first CalVer release.

### Fixed

- Fixed a release issue.

### Supported Versions

- Python: stale value

## [0.6.1] - 2026-08-06

### Fixed

- An older fix.
"""

GENERATED_NOTES = """## What's Changed

* Fix something by @regular in #100

## New Contributors

* @first-timer made their first contribution in #101

**Full Changelog**: https://github.com/example/project/compare/v0.6.1...v2026.08.1
"""


class ReleaseNotesTests(unittest.TestCase):

    def test_extracts_tagged_changelog_entry_without_supported_versions(self):
        entry = release_notes.changelog_entry(CHANGELOG, '2026.08.1')

        self.assertIn('The first CalVer release.', entry)
        self.assertIn('Fixed a release issue.', entry)
        self.assertNotIn('Supported Versions', entry)
        self.assertNotIn('An older fix.', entry)

    def test_build_preserves_existing_notes_and_generates_support_block(self):
        body = release_notes.build_release_body(
            'v2026.08.1',
            CHANGELOG,
            SUPPORT,
            '### New Contributors\n\n* Example contributor',
            GENERATED_NOTES,
        )

        self.assertIn('# v2026.08.1', body)
        self.assertIn('The first CalVer release.', body)
        self.assertIn('### New Contributors', body)
        self.assertIn('@first-timer made their first contribution', body)
        self.assertIn('**Full Changelog**:', body)
        self.assertNotIn("Fix something by @regular", body)
        self.assertIn('- Python: 3.12, 3.13', body)
        self.assertEqual(body.count('### Supported Versions'), 1)

    def test_rebuilding_generated_body_is_idempotent(self):
        first = release_notes.build_release_body(
            'v2026.08.1', CHANGELOG, SUPPORT, 'Manual note', GENERATED_NOTES
        )
        second = release_notes.build_release_body(
            'v2026.08.1', CHANGELOG, SUPPORT, first, GENERATED_NOTES
        )

        self.assertEqual(second, first)

    def test_generated_footer_omits_whats_changed(self):
        footer = release_notes.github_generated_footer(GENERATED_NOTES)

        self.assertIn('## New Contributors', footer)
        self.assertIn('**Full Changelog**:', footer)
        self.assertNotIn("What's Changed", footer)

    def test_missing_version_fails(self):
        with self.assertRaisesRegex(ValueError, 'found 0'):
            release_notes.changelog_entry(CHANGELOG, '2026.09.1')


if __name__ == '__main__':
    unittest.main()
