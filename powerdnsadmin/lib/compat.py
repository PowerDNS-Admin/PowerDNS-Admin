"""Compatibility helpers for modules removed in Python 3.12."""

try:  # Python < 3.12
    from distutils.util import strtobool
except ModuleNotFoundError:  # Python >= 3.12
    from setuptools._distutils.util import strtobool

try:  # Python < 3.12
    from distutils.version import StrictVersion  # type: ignore
except ModuleNotFoundError:  # Python >= 3.12
    from packaging.version import Version as StrictVersion  # noqa: F401

__all__ = ["strtobool", "StrictVersion"]
