#!/usr/bin/env python3
"""Validate a PowerDNS-Admin CalVer release tag and packaged version."""

import argparse
import re
from pathlib import Path


CALVER_TAG = re.compile(
    r"^v(?P<year>[0-9]{4})\.(?P<month>0[1-9]|1[0-2])\."
    r"(?P<release>[1-9][0-9]*)$"
)


def validate(tag, version):
    match = CALVER_TAG.fullmatch(tag)
    if match is None:
        raise ValueError(
            "release tag must use vYYYY.MM.Release with a zero-padded "
            "month and a release counter starting at 1 "
            "(for example, v2026.08.1)"
        )

    expected_version = tag.removeprefix("v")
    if version != expected_version:
        raise ValueError(
            f"powerdnsadmin/VERSION contains {version!r}; expected "
            f"{expected_version!r} for tag {tag!r}"
        )

    return expected_version


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tag", help="Git release tag, including its v prefix")
    parser.add_argument(
        "--version-file",
        type=Path,
        default=Path("powerdnsadmin/VERSION"),
        help="file containing the application version",
    )
    args = parser.parse_args()

    try:
        version = args.version_file.read_text(encoding="utf-8").strip()
        validated_version = validate(args.tag, version)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    print(f"Validated CalVer release {validated_version}")


if __name__ == "__main__":
    main()
