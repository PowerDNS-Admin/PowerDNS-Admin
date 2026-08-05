#!/usr/bin/env python3
"""Append the supported-version block to a GitHub release body once."""

import argparse
import json
import re
from pathlib import Path


START_MARKER = '<!-- supported-versions:start -->'
END_MARKER = '<!-- supported-versions:end -->'
BLOCK_PATTERN = re.compile(
    rf'\n?{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}',
    re.DOTALL,
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--event', required=True, type=Path)
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


def main():
    args = parse_args()
    event = json.loads(args.event.read_text())
    support = json.loads(args.support.read_text())
    current_body = event['release'].get('body') or ''
    current_body = BLOCK_PATTERN.sub('', current_body).rstrip()
    block = supported_versions_block(support)
    updated_body = f'{current_body}\n\n{block}\n' if current_body else f'{block}\n'
    args.output.write_text(json.dumps({'body': updated_body}) + '\n')


if __name__ == '__main__':
    main()
