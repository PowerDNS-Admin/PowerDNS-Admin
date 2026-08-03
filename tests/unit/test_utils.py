import pytest

from powerdnsadmin.lib import utils


@pytest.mark.parametrize('value', [
    True,
    '1',
    'true',
    'TRUE',
    ' t ',
    'yes',
    'y',
    'on',
])
def test_parse_boolean_accepts_true_values(value):
    assert utils.parse_boolean(value) is True


@pytest.mark.parametrize('value', [
    False,
    '0',
    'false',
    'FALSE',
    ' f ',
    'no',
    'n',
    'off',
])
def test_parse_boolean_accepts_false_values(value):
    assert utils.parse_boolean(value) is False


def test_parse_boolean_rejects_unknown_values():
    with pytest.raises(ValueError, match='invalid truth value'):
        utils.parse_boolean('sometimes')


def test_display_record_name_treats_domain_as_literal_text():
    assert utils.display_record_name(
        ('www.example.org', 'example.org')) == 'www'
    assert utils.display_record_name(
        ('www.exampleXorg', 'example.org')) == 'www.exampleXorg'
    assert utils.display_record_name(
        ('example.org', 'example.org')) == '@'
