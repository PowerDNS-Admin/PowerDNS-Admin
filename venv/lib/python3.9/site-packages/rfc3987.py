#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 Daniel Gerber.
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

r"""
Parsing and validation of URIs (RFC 3986) and IRIs (RFC 3987).

This module provides regular expressions according to `RFC 3986 "Uniform
Resource Identifier (URI): Generic Syntax"
<http://tools.ietf.org/html/rfc3986>`_ and `RFC 3987 "Internationalized
Resource Identifiers (IRIs)" <http://tools.ietf.org/html/rfc3987>`_, and
utilities for composition and relative resolution of references.


API
---

**match** (string, rule='IRI_reference')
    {match.__doc__}

**parse** (string, rule='IRI_reference')
    {parse.__doc__}

**compose** (\*\*parts)
    {compose.__doc__}

**resolve** (base, uriref, strict=True, return_parts=False)
    {resolve.__doc__}

**patterns**
    A dict of regular expressions with useful group names.
    Compilable (with regex_ only) without need for any particular compilation
    flag.

**[bmp_][u]patterns[_no_names]**
    Alternative versions of `patterns`.
    [u]nicode strings without group names for the re_ module.
    BMP only for narrow builds.

**get_compiled_pattern** (rule, flags=0)
    {get_compiled_pattern.__doc__}

**format_patterns** (\*\*names)
    {format_patterns.__doc__}


Dependencies
------------

Some features require regex_.

This package's docstrings are tested on python 2.6, 2.7, and 3.2 to 3.6.
Note that in python<=3.2, characters beyond the Basic Multilingual Plane are
not supported on narrow builds (see `issue12729
<http://bugs.python.org/issue12729>`_).


Release notes
-------------

version 1.3.8:

- fixed deprecated escape sequence

version 1.3.6:

- fixed a bug in IPv6 pattern:

  >>> assert match('::0:0:0:0:0.0.0.0', 'IPv6address')

version 1.3.4:

- allowed for lower case percent encoding

version 1.3.3:

- fixed a bug in `resolve` which left "../" at the beginning of some paths

version 1.3.2:

- convenience function `match`
- patterns restricted to the BMP for narrow builds
- adapted doctests for python 3.3
- compatibility with python 2.6 (thanks to Thijs Janssen)

version 1.3.1:

- some re_ compatibility: get_compiled_pattern, parse
- dropped regex_ from setup.py requirements

version 1.3.0:

- python 3.x compatibility
- format_patterns

version 1.2.1:

- compose, resolve


.. _re: http://docs.python.org/library/re
.. _regex: http://pypi.python.org/pypi/regex


Support
-------
This is free software. You may show your appreciation with a `donation`_.

.. _donation: http://danielgerber.net/¤#Thanks-for-python-package-rfc3987

"""
__version__ = '1.3.8'

import sys as _sys

NARROW_BUILD = _sys.maxunicode == 0xffff

try:
    basestring
except NameError:
    basestring = str

try:
    import regex as _re
    REGEX = True
except ImportError:
    import re as _re
    REGEX = False

__all__ = ('get_compiled_pattern', 'parse', 'format_patterns', 'patterns',
           'compose', 'resolve', 'match')


_common_rules = (

    ########   SCHEME   ########
    ('scheme',       r"[a-zA-Z][a-zA-Z0-9+.-]*"),

    ########   PORT   ########
    ('port',         r"[0-9]*"),

    ########   IP ADDRESSES   ########
    ('IP_literal',   r"\[(?:{IPv6address}|{IPvFuture})\]"),
    ('IPv6address', (r"(?:                             (?:{h16}:){{6}} {ls32}"
                     r"|                            :: (?:{h16}:){{5}} {ls32}"
                     r"| (?:                {h16})? :: (?:{h16}:){{4}} {ls32}"
                     r"| (?:(?:{h16}:)?     {h16})? :: (?:{h16}:){{3}} {ls32}"
                     r"| (?:(?:{h16}:){{,2}}{h16})? :: (?:{h16}:){{2}} {ls32}"
                     r"| (?:(?:{h16}:){{,3}}{h16})? :: (?:{h16}:)      {ls32}"
                     r"| (?:(?:{h16}:){{,4}}{h16})? ::                 {ls32}"
                     r"| (?:(?:{h16}:){{,5}}{h16})? ::                 {h16} "
                     r"| (?:(?:{h16}:){{,6}}{h16})? ::                      )"
                      ).replace(' ', '')),
    ('ls32',         r"(?:{h16}:{h16}|{IPv4address})"),
    ('h16',          r"{hexdig}{{1,4}}"),
    ('IPv4address',  r"(?:{dec_octet}\.){{3}}{dec_octet}"),
    ('dec_octet',    r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"),
    ('IPvFuture',    r"v{hexdig}+\.(?:{unreserved}|{sub_delims}|:)+"),

    ########  CHARACTER CLASSES   ########
    ('unreserved',    r"[a-zA-Z0-9_.~-]"),
    ('reserved',      r"(?:{gen_delims}|{sub_delims})"),
    ('pct_encoded',   r"%{hexdig}{{2}}"),
    ('gen_delims',    r"[:/?#[\]@]"),
    ('sub_delims',    r"[!$&'()*+,;=]"),
    ('hexdig',        r"[0-9A-Fa-f]"),

)


_uri_rules = (

    ########   REFERENCES   ########
    ('URI_reference',   r"(?:{URI}|{relative_ref})"),
    ('URI',             r"{absolute_URI}(?:\#{fragment})?"),
    ('absolute_URI',    r"{scheme}:{hier_part}(?:\?{query})?"),
    ('relative_ref',    r"{relative_part}(?:\?{query})?(?:\#{fragment})?"),

    ('hier_part',      (r"(?://{authority}{path_abempty}"
                        r"|{path_absolute}|{path_rootless}|{path_empty})")),
    ('relative_part',  (r"(?://{authority}{path_abempty}"
                        r"|{path_absolute}|{path_noscheme}|{path_empty})")),

    ########   AUTHORITY   ########
    ('authority', r"(?:{userinfo}@)?{host}(?::{port})?"),
    ('host',      r"(?:{IP_literal}|{IPv4address}|{reg_name})"),
    ('userinfo',  r"(?:{unreserved}|{pct_encoded}|{sub_delims}|:)*"),
    ('reg_name',  r"(?:{unreserved}|{pct_encoded}|{sub_delims})*"),

    ########   PATH   ########
    ('path',         (r"(?:{path_abempty}|{path_absolute}|{path_noscheme}"
                      r"|{path_rootless}|{path_empty})")),
    ('path_abempty',  r"(?:/{segment})*"),
    ('path_absolute', r"/(?:{segment_nz}(?:/{segment})*)?"),
    ('path_noscheme', r"{segment_nz_nc}(?:/{segment})*"),
    ('path_rootless', r"{segment_nz}(?:/{segment})*"),
    ('path_empty',    r""),

    ('segment',       r"{pchar}*"),
    ('segment_nz',    r"{pchar}+"),
    ('segment_nz_nc', r"(?:{unreserved}|{pct_encoded}|{sub_delims}|@)+"),

    ########   QUERY   ########
    ('query',         r"(?:{pchar}|/|\?)*"),

    ########   FRAGMENT   ########
    ('fragment',      r"(?:{pchar}|/|\?)*"),

    ########  CHARACTER CLASSES   ########
    ('pchar',         r"(?:{unreserved}|{pct_encoded}|{sub_delims}|:|@)"),

)


#: http://tools.ietf.org/html/rfc3987
#: January 2005
_iri_rules = (

    ########   REFERENCES   ########
    ('IRI_reference',   r"(?:{IRI}|{irelative_ref})"),
    ('IRI',             r"{absolute_IRI}(?:\#{ifragment})?"),
    ('absolute_IRI',    r"{scheme}:{ihier_part}(?:\?{iquery})?"),
    ('irelative_ref',  (r"(?:{irelative_part}"
                        r"(?:\?{iquery})?(?:\#{ifragment})?)")),

    ('ihier_part',     (r"(?://{iauthority}{ipath_abempty}"
                        r"|{ipath_absolute}|{ipath_rootless}|{ipath_empty})")),
    ('irelative_part', (r"(?://{iauthority}{ipath_abempty}"
                        r"|{ipath_absolute}|{ipath_noscheme}|{ipath_empty})")),


    ########   AUTHORITY   ########
    ('iauthority', r"(?:{iuserinfo}@)?{ihost}(?::{port})?"),
    ('iuserinfo',  r"(?:{iunreserved}|{pct_encoded}|{sub_delims}|:)*"),
    ('ihost',      r"(?:{IP_literal}|{IPv4address}|{ireg_name})"),

    ('ireg_name',  r"(?:{iunreserved}|{pct_encoded}|{sub_delims})*"),

    ########   PATH   ########
    ('ipath',         (r"(?:{ipath_abempty}|{ipath_absolute}|{ipath_noscheme}"
                       r"|{ipath_rootless}|{ipath_empty})")),

    ('ipath_empty',    r""),
    ('ipath_rootless', r"{isegment_nz}(?:/{isegment})*"),
    ('ipath_noscheme', r"{isegment_nz_nc}(?:/{isegment})*"),
    ('ipath_absolute', r"/(?:{isegment_nz}(?:/{isegment})*)?"),
    ('ipath_abempty',  r"(?:/{isegment})*"),

    ('isegment_nz_nc', r"(?:{iunreserved}|{pct_encoded}|{sub_delims}|@)+"),
    ('isegment_nz',    r"{ipchar}+"),
    ('isegment',       r"{ipchar}*"),

    ########   QUERY   ########
    ('iquery',    r"(?:{ipchar}|{iprivate}|/|\?)*"),

    ########   FRAGMENT   ########
    ('ifragment', r"(?:{ipchar}|/|\?)*"),

    ########   CHARACTER CLASSES   ########
    ('ipchar',      r"(?:{iunreserved}|{pct_encoded}|{sub_delims}|:|@)"),
    ('iunreserved', r"(?:[a-zA-Z0-9._~-]|{ucschar})"),
    ('iprivate', r"[\uE000-\uF8FF\U000F0000-\U000FFFFD\U00100000-\U0010FFFD]"),
    ('ucschar', (r"[\xA0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF"
                 r"\U00010000-\U0001FFFD\U00020000-\U0002FFFD"
                 r"\U00030000-\U0003FFFD\U00040000-\U0004FFFD"
                 r"\U00050000-\U0005FFFD\U00060000-\U0006FFFD"
                 r"\U00070000-\U0007FFFD\U00080000-\U0008FFFD"
                 r"\U00090000-\U0009FFFD\U000A0000-\U000AFFFD"
                 r"\U000B0000-\U000BFFFD\U000C0000-\U000CFFFD"
                 r"\U000D0000-\U000DFFFD\U000E1000-\U000EFFFD]")),

)


def format_patterns(**names):
    r"""Returns a dict of patterns (regular expressions) keyed by
    `rule names for URIs`_ and `rule names for IRIs`_.

    See also the module level dicts of patterns, and `get_compiled_pattern`.

    To wrap a rule in a named capture group, pass it as keyword argument:
    rule_name='group_name'. By default, the formatted patterns contain no
    named groups.

    Patterns are `str` instances (be it in python 2.x or 3.x) containing ASCII
    characters only.

    Caveats:

      - with re_, named capture groups cannot occur on multiple branches of an
        alternation

      - with re_ before python 3.3, ``\u`` and ``\U`` escapes must be
        preprocessed (see `issue3665 <http://bugs.python.org/issue3665>`_)

      - on narrow builds, character ranges beyond BMP are not supported

    .. _rule names for URIs: http://tools.ietf.org/html/rfc3986#appendix-A
    .. _rule names for IRIs: http://tools.ietf.org/html/rfc3987#section-2.2
    """
    formatted = {}
    for name, pat in _common_rules[::-1] + _uri_rules[::-1] + _iri_rules[::-1]:
        if name in names:
            n = names[name]
            if callable(n):
                pat = n(pat)
            else:
                pat = '(?P<%s>%s)' % (n, pat)
        formatted[name] = pat.format(**formatted)
    return formatted


_GROUP_NAMES_BASE = [
        'scheme', 'port',
        'IPv6address', 'IPv4address', 'IPvFuture',
        'URI_reference',
        'URI', 'absolute_URI', 'relative_ref', 'relative_part',
        'authority', 'host', 'userinfo', 'reg_name',
        'query', 'fragment',
        'IRI_reference',
        'IRI', 'absolute_IRI', 'irelative_ref', 'irelative_part',
        'iauthority', 'ihost', 'iuserinfo', 'ireg_name',
        'iquery', 'ifragment'
        ]

DEFAULT_GROUP_NAMES = dict(zip(_GROUP_NAMES_BASE,_GROUP_NAMES_BASE),
    path_abempty='path', path_absolute='path', path_noscheme='path',
    path_rootless='path', path_empty='path',
    ipath_abempty='ipath', ipath_absolute='ipath', ipath_noscheme='ipath',
    ipath_rootless='ipath', ipath_empty='ipath')

#: mapping of rfc3986 / rfc3987 rule names to regular expressions
patterns = format_patterns(**DEFAULT_GROUP_NAMES)


def _interpret_unicode_escapes(string):
    return string.encode('ascii').decode('raw-unicode-escape')

patterns_no_names = format_patterns()

# if not REGEX:
#: patterns compilable with re
upatterns_no_names = dict((k, _interpret_unicode_escapes(v)) for k,v
                          in format_patterns().items())

_bmp = lambda s: _re.sub(r'\\U[0-9A-F]{8}-\\U[0-9A-F]{8}', '', s)
#: patterns restricted to the basic multilingual plane
#: compilable on narrow build
bmp_patterns = dict((k, _bmp(v)) for k,v in patterns.items())
#: compilable on narrow build with re
bmp_upatterns_no_names = dict((k, _interpret_unicode_escapes(_bmp(v)))
                              for k,v in patterns_no_names.items())


def get_compiled_pattern(rule, flags=0):
    """Returns a compiled pattern object for a rule name or template string.

    Usage for validation::

        >>> uri = get_compiled_pattern('^%(URI)s$')
        >>> assert uri.match('http://tools.ietf.org/html/rfc3986#appendix-A')
        >>> assert not get_compiled_pattern('^%(relative_ref)s$').match('#f#g')
        >>> from unicodedata import lookup
        >>> smp = 'urn:' + lookup('OLD ITALIC LETTER A')  # U+00010300
        >>> assert not uri.match(smp)
        >>> m = get_compiled_pattern('^%(IRI)s$').match(smp)

    On narrow builds, non-BMP characters are (incorrectly) excluded::

        >>> assert NARROW_BUILD == (not m)

    For parsing, some subcomponents are captured in named groups (*only if*
    regex_ is available, otherwise see `parse`)::

        >>> match = uri.match('http://tools.ietf.org/html/rfc3986#appendix-A')
        >>> d = match.groupdict()
        >>> if REGEX:
        ...     assert all([ d['scheme'] == 'http',
        ...                  d['authority'] == 'tools.ietf.org',
        ...                  d['path'] == '/html/rfc3986',
        ...                  d['query'] == None,
        ...                  d['fragment'] == 'appendix-A' ])

        >>> for r in patterns.keys():
        ...     assert get_compiled_pattern(r)

    """
    cache, key = get_compiled_pattern.cache, (rule, flags)
    if key not in cache:
        if NARROW_BUILD:
            pats = bmp_patterns if REGEX else bmp_upatterns_no_names
        else:
            pats = patterns if REGEX else upatterns_no_names
        p = pats.get(rule) or rule % pats
        cache[key] = _re.compile(p, flags)
    return cache[key]
get_compiled_pattern.cache = {}


def match(string, rule='IRI_reference'):
    """Convenience function for checking if `string` matches a specific rule.

    Returns a match object or None::

        >>> assert match('%C7X', 'pct_encoded') is None
        >>> assert match('%C7', 'pct_encoded')
        >>> assert match('%c7', 'pct_encoded')

    """
    return get_compiled_pattern('^%%(%s)s$' % rule).match(string)


#: http://tools.ietf.org/html/rfc3986#appendix-B
_iri_non_validating_re = _re.compile(
    r"^((?P<scheme>[^:/?#]+):)?(//(?P<authority>[^/?#]*))?"
    r"(?P<path>[^?#]*)(\?(?P<query>[^#]*))?(#(?P<fragment>.*))?")

REFERENCE_RULES = ('IRI_reference', 'IRI', 'absolute_IRI',
                   'irelative_ref', 'irelative_part',
                   'URI_reference', 'URI', 'absolute_URI',
                   'relative_ref', 'relative_part')

def parse(string, rule='IRI_reference'):
    """Parses `string` according to `rule` into a dict of subcomponents.

    If `rule` is None, parse an IRI_reference `without validation
    <http://tools.ietf.org/html/rfc3986#appendix-B>`_.

    If regex_ is available, any rule is supported; with re_, `rule` must be
    'IRI_reference' or some special case thereof ('IRI', 'absolute_IRI',
    'irelative_ref', 'irelative_part', 'URI_reference', 'URI', 'absolute_URI',
    'relative_ref', 'relative_part'). ::

        >>> d = parse('http://tools.ietf.org/html/rfc3986#appendix-A',
        ...           rule='URI')
        >>> assert all([ d['scheme'] == 'http',
        ...              d['authority'] == 'tools.ietf.org',
        ...              d['path'] == '/html/rfc3986',
        ...              d['query'] == None,
        ...              d['fragment'] == 'appendix-A' ])

    """
    if not REGEX and rule and rule not in REFERENCE_RULES:
        raise ValueError(rule)
    if rule:
        m = match(string, rule)
        if not m:
            raise ValueError('%r is not a valid %r.' % (string, rule))
        if REGEX:
            return _i2u(m.groupdict())
    return _i2u(_iri_non_validating_re.match(string).groupdict())


def _i2u(dic):
    for (name, iname) in [('authority', 'iauthority'), ('path', 'ipath'),
                          ('query', 'iquery'), ('fragment', 'ifragment')]:
        if dic.get(name) is None:
            dic[name] = dic.get(iname)
    return dic


def compose(scheme=None, authority=None, path=None, query=None, fragment=None,
            iauthority=None, ipath=None, iquery=None, ifragment=None, **kw):
    """Returns an URI composed_ from named parts.

    .. _composed: http://tools.ietf.org/html/rfc3986#section-5.3
    """
    _i2u(locals())
    res = ''
    if scheme is not None:
        res += scheme + ':'
    if authority is not None:
        res += '//' + authority
    res += path or ''
    if query is not None:
        res += '?' + query
    if fragment is not None:
        res += '#' + fragment
    return res


_dot_segments = get_compiled_pattern(r'^(?:\.{1,2}(?:/|$))+|(?<=/)\.(?:/|$)')
_2dots_segments = get_compiled_pattern(r'/?%(segment)s/\.{2}(?:/|$)')

def _remove_dot_segments(path):
    path =  _dot_segments.sub('', path)
    c = 1
    while c:
        path, c =  _2dots_segments.subn('/', path, 1)
    return path


def resolve(base, uriref, strict=True, return_parts=False):
    """Resolves_ an `URI reference` relative to a `base` URI.

    `Test cases <http://tools.ietf.org/html/rfc3986#section-5.4>`_::

        >>> base = resolve.test_cases_base
        >>> for relative, resolved in resolve.test_cases.items():
        ...     assert resolve(base, relative) == resolved

    If `return_parts` is True, returns a dict of named parts instead of
    a string.

    Examples::

        >>> assert resolve('urn:rootless', '../../name') == 'urn:name'
        >>> assert resolve('urn:root/less', '../../name') == 'urn:/name'
        >>> assert resolve('http://a/b', 'http:g') == 'http:g'
        >>> assert resolve('http://a/b', 'http:g', strict=False) == 'http://a/g'

    .. _Resolves: http://tools.ietf.org/html/rfc3986#section-5.2

    """
    #base = normalize(base)
    if isinstance(base, basestring):
        B = parse(base, 'IRI')
    else:
        B = _i2u(dict(base))
    if not B.get('scheme'):
        raise ValueError('Expected an IRI (with scheme), not %r.' % base)

    if isinstance(uriref, basestring):
        R = parse(uriref, 'IRI_reference')
    else:
        R = _i2u(dict(uriref))

    # _last_segment = get_compiled_pattern(r'(?<=^|/)%(segment)s$')

    if R['scheme'] and (strict or R['scheme'] != B['scheme']):
        T = R
    else:
        T = {}
        T['scheme'] = B['scheme']
        if R['authority'] is not None:
            T['authority'] = R['authority']
            T['path'] = R['path']
            T['query'] = R['query']
        else:
            T['authority'] = B['authority']
            if R['path']:
                if R['path'][:1] == "/":
                    T['path'] = R['path']
                elif B['authority'] is not None and not B['path']:
                    T['path'] = '/%s' % R['path']
                else:
                    T['path'] = ''.join(B['path'].rpartition('/')[:2]) + R['path']
                    # _last_segment.sub(R['path'], B['path'])
                T['query'] = R['query']
            else:
                T['path'] = B['path']
                if R['query'] is not None:
                    T['query'] = R['query']
                else:
                    T['query'] = B['query']
        T['fragment'] = R['fragment']
    T['path'] = _remove_dot_segments(T['path'])
    if return_parts:
        return T
    else:
        return compose(**T)

resolve.test_cases_base = "http://a/b/c/d;p?q"
resolve.test_cases = {
    "g:h"           :  "g:h",
    "g"             :  "http://a/b/c/g",
    "./g"           :  "http://a/b/c/g",
    "g/"            :  "http://a/b/c/g/",
    "/g"            :  "http://a/g",
    "//g"           :  "http://g",
    "?y"            :  "http://a/b/c/d;p?y",
    "g?y"           :  "http://a/b/c/g?y",
    "#s"            :  "http://a/b/c/d;p?q#s",
    "g#s"           :  "http://a/b/c/g#s",
    "g?y#s"         :  "http://a/b/c/g?y#s",
    ";x"            :  "http://a/b/c/;x",
    "g;x"           :  "http://a/b/c/g;x",
    "g;x?y#s"       :  "http://a/b/c/g;x?y#s",
    ""              :  "http://a/b/c/d;p?q",
    "."             :  "http://a/b/c/",
    "./"            :  "http://a/b/c/",
    ".."            :  "http://a/b/",
    "../"           :  "http://a/b/",
    "../g"          :  "http://a/b/g",
    "../.."         :  "http://a/",
    "../../"        :  "http://a/",
    "../../g"       :  "http://a/g",
    "../../../g"    :  "http://a/g",
    "../../../../g" :  "http://a/g",
    "/./g"          :  "http://a/g",
    "/../g"         :  "http://a/g",
    "g."            :  "http://a/b/c/g.",
    ".g"            :  "http://a/b/c/.g",
    "g.."           :  "http://a/b/c/g..",
    "..g"           :  "http://a/b/c/..g",
    "./../g"        :  "http://a/b/g",
    "./g/."         :  "http://a/b/c/g/",
    "g/./h"         :  "http://a/b/c/g/h",
    "g/../h"        :  "http://a/b/c/h",
    "g;x=1/./y"     :  "http://a/b/c/g;x=1/y",
    "g;x=1/../y"    :  "http://a/b/c/y",
    "g?y/./x"       :  "http://a/b/c/g?y/./x",
    "g?y/../x"      :  "http://a/b/c/g?y/../x",
    "g#s/./x"       :  "http://a/b/c/g#s/./x",
    "g#s/../x"      :  "http://a/b/c/g#s/../x",
    }


def normalize(uri):
    "Syntax-Based Normalization"
    # TODO:
    raise NotImplementedError


if __name__ == '__main__':
    if not _sys.argv[1:]:
        print('Valid arguments are "--all" or rule names from:')
        print('  '.join(sorted(patterns)))
    elif _sys.argv[1] == '--all':
        for name in patterns:
            print(name + ':')
            print(patterns[name])
    else:
        for name in _sys.argv[1:]:
            print(patterns[name])
