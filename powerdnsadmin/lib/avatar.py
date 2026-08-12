"""Helpers for generated and fallback user avatars."""

from __future__ import annotations

import html

# Readable Bootstrap-adjacent fills for white initials text.
_AVATAR_COLORS = (
    '#0d6efd',
    '#6610f2',
    '#6f42c1',
    '#d63384',
    '#dc3545',
    '#fd7e14',
    '#198754',
    '#20c997',
    '#0dcaf0',
    '#6c757d',
)


def avatar_initials(firstname=None, lastname=None, username=None):
    """Return up to two alphanumeric initials for an avatar label."""
    first = (firstname or '').strip()
    last = (lastname or '').strip()

    if first and last:
        raw = f'{first[0]}{last[0]}'
    elif first:
        raw = first[:2]
    elif last:
        raw = last[:2]
    else:
        raw = (username or '').strip()[:2]

    return ''.join(character for character in raw.upper() if character.isalnum())[:2]


def avatar_color(seed):
    """Pick a stable fill color from a username or other seed string."""
    value = seed or ''
    index = sum(ord(character) for character in value) % len(_AVATAR_COLORS)
    return _AVATAR_COLORS[index]


def initials_avatar_svg(initials, seed=None):
    """Return an SVG avatar with the given initials."""
    label = ''.join(
        character for character in (initials or '').upper() if character.isalnum())[:2]
    if not label:
        raise ValueError('initials are required')

    color = avatar_color(seed or label)
    safe_label = html.escape(label, quote=True)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" role="img" '
        f'aria-label="Avatar for {safe_label}">'
        f'<circle cx="64" cy="64" r="64" fill="{color}"/>'
        '<text x="64" y="64" dy="0.08em" fill="#ffffff" font-family="'
        'system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif" '
        'font-size="56" font-weight="600" text-anchor="middle" '
        f'dominant-baseline="middle">{safe_label}</text>'
        '</svg>'
    )
