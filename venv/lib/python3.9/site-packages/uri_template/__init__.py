"""Module to implement something."""

from typing import Optional

from .expansions import ExpansionFailedError
from .uritemplate import ExpansionInvalidError, ExpansionReservedError, URITemplate
from .variable import Variable, VariableInvalidError


__all__ = [
    'URITemplate', 'Variable',
    'ExpansionInvalidError', 'ExpansionReservedError', 'VariableInvalidError', 'ExpansionFailedError',
]


def expand(template: str, **kwargs) -> Optional[str]:
    try:
        templ = URITemplate(template)
        return templ.expand(**kwargs)
    except Exception:
        return None


def partial(template: str, **kwargs) -> Optional[str]:
    try:
        templ = URITemplate(template)
        return str(templ.partial(**kwargs))
    except Exception:
        return None


def validate(template: str) -> bool:
    try:
        URITemplate(template)
        return True
    except Exception:
        return False
