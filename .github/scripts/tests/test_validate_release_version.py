import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / 'validate-release-version.py'
)
SPEC = importlib.util.spec_from_file_location(
    'validate_release_version', SCRIPT_PATH
)
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


class ValidateReleaseVersionTest(unittest.TestCase):
    def test_accepts_first_release_of_a_month(self):
        self.assertEqual(
            validator.validate('v2026.11.0', '2026.11.0'),
            '2026.11.0',
        )

    def test_accepts_later_release_in_the_same_month(self):
        self.assertEqual(
            validator.validate('v2026.08.1', '2026.08.1'),
            '2026.08.1',
        )

    def test_rejects_a_release_counter_with_a_leading_zero(self):
        with self.assertRaises(ValueError):
            validator.validate('v2026.11.00', '2026.11.00')

    def test_rejects_an_unpadded_month(self):
        with self.assertRaises(ValueError):
            validator.validate('v2026.8.0', '2026.8.0')

    def test_rejects_a_version_file_that_does_not_match_the_tag(self):
        with self.assertRaises(ValueError):
            validator.validate('v2026.11.0', 'DEV-2026.11.0')


if __name__ == '__main__':
    unittest.main()
