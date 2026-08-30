#!/usr/bin/env python3
"""Build a GitHub release body from CHANGELOG.md and supported versions."""

import argparse
import json
import re
from pathlib import Path


START_MARKER = '<!-- supported-versions:start -->'
END_MARKER = '<!-- supported-versions:end -->'
CHANGELOG_START_MARKER = '<!-- changelog-entry:start -->'
CHANGELOG_END_MARKER = '<!-- changelog-entry:end -->'
GITHUB_NOTES_START_MARKER = '<!-- github-generated-notes:start -->'
GITHUB_NOTES_END_MARKER = '<!-- github-generated-notes:end -->'
BLOCK_PATTERN = re.compile(
    rf'\n?{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}',
    re.DOTALL,
)
CHANGELOG_BLOCK_PATTERN = re.compile(
    rf'\n?{re.escape(CHANGELOG_START_MARKER)}.*?'
    rf'{re.escape(CHANGELOG_END_MARKER)}',
    re.DOTALL,
)
GITHUB_NOTES_BLOCK_PATTERN = re.compile(
    rf'\n?{re.escape(GITHUB_NOTES_START_MARKER)}.*?'
    rf'{re.escape(GITHUB_NOTES_END_MARKER)}',
    re.DOTALL,
)
CHANGELOG_HEADING_PATTERN = re.compile(
    r'^## \[(?P<version>[^]]+)](?: - \d{4}-\d{2}-\d{2})?\s*$',
    re.MULTILINE,
)
SUPPORTED_VERSIONS_SECTION_PATTERN = re.compile(
    r'^### Supported Versions\s*$.*?(?=^### |\Z)',
    re.MULTILINE | re.DOTALL,
)
NEW_CONTRIBUTORS_PATTERN = re.compile(
    r'^#{2,3} New Contributors\s*$.*?'
    r'(?=^\*\*Full Changelog\*\*:|^Full Changelog:|\Z)',
    re.MULTILINE | re.DOTALL,
)
FULL_CHANGELOG_PATTERN = re.compile(
    r'^(?:\*\*Full Changelog\*\*|Full Changelog):[^\n]*$',
    re.MULTILINE,
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--event', required=True, type=Path)
    parser.add_argument('--changelog', required=True, type=Path)
    parser.add_argument('--generated-notes', required=True, type=Path)
    parser.add_argument('--support', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    return parser.parse_args()


def display_name(identifier):
    return identifier.replace('_', ' ').title()


def supported_versions_block(support):
    python_versions = ', '.join(support['python']['supported_versions'])
    browser_versions = ', '.join(
        f"{display_name(name)} {details['minimum_version']}+"
        for name, details in support['browsers'].items()
    )
    powerdns_versions = ', '.join(
        support['powerdns_auth']['supported_versions']
    )

    return '\n'.join((
        START_MARKER,
        '### Supported Versions',
        '',
        f'- Python: {python_versions}',
        f'- Browsers: {browser_versions}',
        f'- PowerDNS Authoritative Server: {powerdns_versions}',
        END_MARKER,
    ))


def release_version(tag):
    if not tag.startswith('v') or len(tag) == 1:
        raise ValueError(f'release tag must start with v: {tag!r}')
    return tag[1:]


def changelog_entry(changelog, version):
    matches = [
        match for match in CHANGELOG_HEADING_PATTERN.finditer(changelog)
        if match.group('version') == version
    ]
    if len(matches) != 1:
        raise ValueError(
            f'expected exactly one CHANGELOG.md entry for {version!r}; '
            f'found {len(matches)}'
        )

    match = matches[0]
    next_heading = CHANGELOG_HEADING_PATTERN.search(changelog, match.end())
    end = next_heading.start() if next_heading else len(changelog)
    entry = changelog[match.end():end].strip()
    entry = SUPPORTED_VERSIONS_SECTION_PATTERN.sub('', entry).strip()
    if not entry:
        raise ValueError(f'CHANGELOG.md entry for {version!r} is empty')
    return entry


def generated_changelog_block(tag, entry):
    return '\n'.join((
        CHANGELOG_START_MARKER,
        f'# {tag}',
        '',
        entry,
        CHANGELOG_END_MARKER,
    ))


def github_generated_footer(generated_body):
    sections = []
    contributors = NEW_CONTRIBUTORS_PATTERN.search(generated_body)
    if contributors:
        sections.append(contributors.group(0).strip())
    full_changelog = FULL_CHANGELOG_PATTERN.search(generated_body)
    if full_changelog:
        sections.append(full_changelog.group(0).strip())
    if not sections:
        return ''

    return '\n'.join((
        GITHUB_NOTES_START_MARKER,
        '\n\n'.join(sections),
        GITHUB_NOTES_END_MARKER,
    ))


def build_release_body(tag, changelog, support, current_body='',
                       generated_body=''):
    version = release_version(tag)
    entry = changelog_entry(changelog, version)
    preserved_body = CHANGELOG_BLOCK_PATTERN.sub('', current_body)
    preserved_body = BLOCK_PATTERN.sub('', preserved_body).strip()
    preserved_body = GITHUB_NOTES_BLOCK_PATTERN.sub('', preserved_body).strip()

    sections = [generated_changelog_block(tag, entry)]
    if preserved_body:
        sections.append(preserved_body)
    generated_footer = github_generated_footer(generated_body)
    if generated_footer:
        sections.append(generated_footer)
    sections.append(supported_versions_block(support))
    return '\n\n'.join(sections) + '\n'


def main():
    args = parse_args()
    event = json.loads(args.event.read_text())
    changelog = args.changelog.read_text(encoding='utf-8')
    generated_notes = json.loads(args.generated_notes.read_text())
    support = json.loads(args.support.read_text())
    current_body = event['release'].get('body') or ''
    tag = event['release']['tag_name']
    updated_body = build_release_body(
        tag, changelog, support, current_body, generated_notes.get('body') or ''
    )
    args.output.write_text(json.dumps({'body': updated_body}) + '\n')


if __name__ == '__main__':
    main()
