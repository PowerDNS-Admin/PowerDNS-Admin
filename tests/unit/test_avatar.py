from powerdnsadmin.lib.avatar import (
    avatar_color,
    avatar_initials,
    initials_avatar_svg,
)


def test_avatar_initials_prefer_first_and_last_name():
    assert avatar_initials('Ada', 'Lovelace', 'alovelace') == 'AL'


def test_avatar_initials_fall_back_to_single_name_then_username():
    assert avatar_initials('Ada', '', 'alovelace') == 'AD'
    assert avatar_initials('', 'Lovelace', 'alovelace') == 'LO'
    assert avatar_initials('', '', 'admin') == 'AD'
    assert avatar_initials('', '', 'a') == 'A'


def test_avatar_initials_strip_non_alphanumeric_characters():
    assert avatar_initials("O'Neil", 'Smith', 'oneil') == 'OS'
    assert avatar_initials('', '', '@@') == ''


def test_avatar_color_is_stable_for_the_same_seed():
    assert avatar_color('alice') == avatar_color('alice')
    assert avatar_color('alice') != avatar_color('bob')


def test_initials_avatar_svg_embeds_label_and_fill():
    svg = initials_avatar_svg('AL', seed='alice')

    assert 'image/svg+xml' not in svg
    assert '>AL</text>' in svg
    assert f'fill="{avatar_color("alice")}"' in svg
    assert 'Avatar for AL' in svg
