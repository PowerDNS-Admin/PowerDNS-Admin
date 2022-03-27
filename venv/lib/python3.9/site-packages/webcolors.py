"""
Utility functions for working with the color names and color value
formats defined by the HTML and CSS specifications for use in
documents on the Web.

See documentation (in docs/ directory of source distribution) for
details of the supported formats, conventions and conversions.

"""

import re
import string
from typing import NamedTuple, Tuple, Union


__version__ = "1.11.1"


def _reversedict(d: dict) -> dict:
    """
    Internal helper for generating reverse mappings; given a
    dictionary, returns a new dictionary with keys and values swapped.

    """
    return {value: key for key, value in d.items()}


HEX_COLOR_RE = re.compile(r"^#([a-fA-F0-9]{3}|[a-fA-F0-9]{6})$")

HTML4 = "html4"
CSS2 = "css2"
CSS21 = "css21"
CSS3 = "css3"

SUPPORTED_SPECIFICATIONS = (HTML4, CSS2, CSS21, CSS3)

SPECIFICATION_ERROR_TEMPLATE = "{{spec}} is not a supported specification for color name lookups; \
supported specifications are: {supported}.".format(
    supported=",".join(SUPPORTED_SPECIFICATIONS)
)

IntegerRGB = NamedTuple("IntegerRGB", [("red", int), ("green", int), ("blue", int)])
PercentRGB = NamedTuple("PercentRGB", [("red", str), ("green", str), ("blue", str)])
HTML5SimpleColor = NamedTuple(
    "HTML5SimpleColor", [("red", int), ("green", int), ("blue", int)]
)

IntTuple = Union[IntegerRGB, HTML5SimpleColor, Tuple[int, int, int]]
PercentTuple = Union[PercentRGB, Tuple[str, str, str]]


# Mappings of color names to normalized hexadecimal color values.
#################################################################

# The HTML 4 named colors.
#
# The canonical source for these color definitions is the HTML 4
# specification:
#
# http://www.w3.org/TR/html401/types.html#h-6.5
#
# The file tests/definitions.py in the source distribution of this
# module downloads a copy of the HTML 4 standard and parses out the
# color names to ensure the values below are correct.
HTML4_NAMES_TO_HEX = {
    "aqua": "#00ffff",
    "black": "#000000",
    "blue": "#0000ff",
    "fuchsia": "#ff00ff",
    "green": "#008000",
    "gray": "#808080",
    "lime": "#00ff00",
    "maroon": "#800000",
    "navy": "#000080",
    "olive": "#808000",
    "purple": "#800080",
    "red": "#ff0000",
    "silver": "#c0c0c0",
    "teal": "#008080",
    "white": "#ffffff",
    "yellow": "#ffff00",
}

# CSS 2 used the same list as HTML 4.
CSS2_NAMES_TO_HEX = HTML4_NAMES_TO_HEX

# CSS 2.1 added orange.
CSS21_NAMES_TO_HEX = {"orange": "#ffa500", **HTML4_NAMES_TO_HEX}

# The CSS 3/SVG named colors.
#
# The canonical source for these color definitions is the SVG
# specification's color list (which was adopted as CSS 3's color
# definition):
#
# http://www.w3.org/TR/SVG11/types.html#ColorKeywords
#
# CSS 3 also provides definitions of these colors:
#
# http://www.w3.org/TR/css3-color/#svg-color
#
# SVG provides the definitions as RGB triplets. CSS 3 provides them
# both as RGB triplets and as hexadecimal. Since hex values are more
# common in real-world HTML and CSS, the mapping below is to hex
# values instead. The file tests/definitions.py in the source
# distribution of this module downloads a copy of the CSS 3 color
# module and parses out the color names to ensure the values below are
# correct.
CSS3_NAMES_TO_HEX = {
    "aliceblue": "#f0f8ff",
    "antiquewhite": "#faebd7",
    "aqua": "#00ffff",
    "aquamarine": "#7fffd4",
    "azure": "#f0ffff",
    "beige": "#f5f5dc",
    "bisque": "#ffe4c4",
    "black": "#000000",
    "blanchedalmond": "#ffebcd",
    "blue": "#0000ff",
    "blueviolet": "#8a2be2",
    "brown": "#a52a2a",
    "burlywood": "#deb887",
    "cadetblue": "#5f9ea0",
    "chartreuse": "#7fff00",
    "chocolate": "#d2691e",
    "coral": "#ff7f50",
    "cornflowerblue": "#6495ed",
    "cornsilk": "#fff8dc",
    "crimson": "#dc143c",
    "cyan": "#00ffff",
    "darkblue": "#00008b",
    "darkcyan": "#008b8b",
    "darkgoldenrod": "#b8860b",
    "darkgray": "#a9a9a9",
    "darkgrey": "#a9a9a9",
    "darkgreen": "#006400",
    "darkkhaki": "#bdb76b",
    "darkmagenta": "#8b008b",
    "darkolivegreen": "#556b2f",
    "darkorange": "#ff8c00",
    "darkorchid": "#9932cc",
    "darkred": "#8b0000",
    "darksalmon": "#e9967a",
    "darkseagreen": "#8fbc8f",
    "darkslateblue": "#483d8b",
    "darkslategray": "#2f4f4f",
    "darkslategrey": "#2f4f4f",
    "darkturquoise": "#00ced1",
    "darkviolet": "#9400d3",
    "deeppink": "#ff1493",
    "deepskyblue": "#00bfff",
    "dimgray": "#696969",
    "dimgrey": "#696969",
    "dodgerblue": "#1e90ff",
    "firebrick": "#b22222",
    "floralwhite": "#fffaf0",
    "forestgreen": "#228b22",
    "fuchsia": "#ff00ff",
    "gainsboro": "#dcdcdc",
    "ghostwhite": "#f8f8ff",
    "gold": "#ffd700",
    "goldenrod": "#daa520",
    "gray": "#808080",
    "grey": "#808080",
    "green": "#008000",
    "greenyellow": "#adff2f",
    "honeydew": "#f0fff0",
    "hotpink": "#ff69b4",
    "indianred": "#cd5c5c",
    "indigo": "#4b0082",
    "ivory": "#fffff0",
    "khaki": "#f0e68c",
    "lavender": "#e6e6fa",
    "lavenderblush": "#fff0f5",
    "lawngreen": "#7cfc00",
    "lemonchiffon": "#fffacd",
    "lightblue": "#add8e6",
    "lightcoral": "#f08080",
    "lightcyan": "#e0ffff",
    "lightgoldenrodyellow": "#fafad2",
    "lightgray": "#d3d3d3",
    "lightgrey": "#d3d3d3",
    "lightgreen": "#90ee90",
    "lightpink": "#ffb6c1",
    "lightsalmon": "#ffa07a",
    "lightseagreen": "#20b2aa",
    "lightskyblue": "#87cefa",
    "lightslategray": "#778899",
    "lightslategrey": "#778899",
    "lightsteelblue": "#b0c4de",
    "lightyellow": "#ffffe0",
    "lime": "#00ff00",
    "limegreen": "#32cd32",
    "linen": "#faf0e6",
    "magenta": "#ff00ff",
    "maroon": "#800000",
    "mediumaquamarine": "#66cdaa",
    "mediumblue": "#0000cd",
    "mediumorchid": "#ba55d3",
    "mediumpurple": "#9370db",
    "mediumseagreen": "#3cb371",
    "mediumslateblue": "#7b68ee",
    "mediumspringgreen": "#00fa9a",
    "mediumturquoise": "#48d1cc",
    "mediumvioletred": "#c71585",
    "midnightblue": "#191970",
    "mintcream": "#f5fffa",
    "mistyrose": "#ffe4e1",
    "moccasin": "#ffe4b5",
    "navajowhite": "#ffdead",
    "navy": "#000080",
    "oldlace": "#fdf5e6",
    "olive": "#808000",
    "olivedrab": "#6b8e23",
    "orange": "#ffa500",
    "orangered": "#ff4500",
    "orchid": "#da70d6",
    "palegoldenrod": "#eee8aa",
    "palegreen": "#98fb98",
    "paleturquoise": "#afeeee",
    "palevioletred": "#db7093",
    "papayawhip": "#ffefd5",
    "peachpuff": "#ffdab9",
    "peru": "#cd853f",
    "pink": "#ffc0cb",
    "plum": "#dda0dd",
    "powderblue": "#b0e0e6",
    "purple": "#800080",
    "red": "#ff0000",
    "rosybrown": "#bc8f8f",
    "royalblue": "#4169e1",
    "saddlebrown": "#8b4513",
    "salmon": "#fa8072",
    "sandybrown": "#f4a460",
    "seagreen": "#2e8b57",
    "seashell": "#fff5ee",
    "sienna": "#a0522d",
    "silver": "#c0c0c0",
    "skyblue": "#87ceeb",
    "slateblue": "#6a5acd",
    "slategray": "#708090",
    "slategrey": "#708090",
    "snow": "#fffafa",
    "springgreen": "#00ff7f",
    "steelblue": "#4682b4",
    "tan": "#d2b48c",
    "teal": "#008080",
    "thistle": "#d8bfd8",
    "tomato": "#ff6347",
    "turquoise": "#40e0d0",
    "violet": "#ee82ee",
    "wheat": "#f5deb3",
    "white": "#ffffff",
    "whitesmoke": "#f5f5f5",
    "yellow": "#ffff00",
    "yellowgreen": "#9acd32",
}


# Mappings of normalized hexadecimal color values to color names.
#################################################################

HTML4_HEX_TO_NAMES = _reversedict(HTML4_NAMES_TO_HEX)

CSS2_HEX_TO_NAMES = HTML4_HEX_TO_NAMES

CSS21_HEX_TO_NAMES = _reversedict(CSS21_NAMES_TO_HEX)

CSS3_HEX_TO_NAMES = _reversedict(CSS3_NAMES_TO_HEX)

# CSS3 defines both 'gray' and 'grey', as well as defining either
# variant for other related colors like 'darkgray'/'darkgrey'. For a
# 'forward' lookup from name to hex, this is straightforward, but a
# 'reverse' lookup from hex to name requires picking one spelling.
#
# The way in which _reversedict() generates the reverse mappings will
# pick a spelling based on the ordering of dictionary keys, which
# varies according to the version and implementation of Python in use,
# and in some Python versions is explicitly not to be relied on for
# consistency. So here we manually pick a single spelling that will
# consistently be returned. Since 'gray' was the only spelling
# supported in HTML 4, CSS1, and CSS2, 'gray' and its varients are
# chosen.
CSS3_HEX_TO_NAMES["#a9a9a9"] = "darkgray"
CSS3_HEX_TO_NAMES["#2f4f4f"] = "darkslategray"
CSS3_HEX_TO_NAMES["#696969"] = "dimgray"
CSS3_HEX_TO_NAMES["#808080"] = "gray"
CSS3_HEX_TO_NAMES["#d3d3d3"] = "lightgray"
CSS3_HEX_TO_NAMES["#778899"] = "lightslategray"
CSS3_HEX_TO_NAMES["#708090"] = "slategray"


# Normalization functions.
#################################################################


def normalize_hex(hex_value: str) -> str:
    """
    Normalize a hexadecimal color value to 6 digits, lowercase.

    """
    match = HEX_COLOR_RE.match(hex_value)
    if match is None:
        raise ValueError(
            "'{}' is not a valid hexadecimal color value.".format(hex_value)
        )
    hex_digits = match.group(1)
    if len(hex_digits) == 3:
        hex_digits = "".join(2 * s for s in hex_digits)
    return "#{}".format(hex_digits.lower())


def _normalize_integer_rgb(value: int) -> int:
    """
    Internal normalization function for clipping integer values into
    the permitted range (0-255, inclusive).

    """
    return 0 if value < 0 else 255 if value > 255 else value


def normalize_integer_triplet(rgb_triplet: IntTuple) -> IntegerRGB:
    """
    Normalize an integer ``rgb()`` triplet so that all values are
    within the range 0-255 inclusive.

    """
    return IntegerRGB._make(_normalize_integer_rgb(value) for value in rgb_triplet)


def _normalize_percent_rgb(value: str) -> str:
    """
    Internal normalization function for clipping percent values into
    the permitted range (0%-100%, inclusive).

    """
    value = value.split("%")[0]
    percent = float(value) if "." in value else int(value)

    return "0%" if percent < 0 else "100%" if percent > 100 else "{}%".format(percent)


def normalize_percent_triplet(rgb_triplet: PercentTuple) -> PercentRGB:
    """
    Normalize a percentage ``rgb()`` triplet so that all values are
    within the range 0%-100% inclusive.

    """
    return PercentRGB._make(_normalize_percent_rgb(value) for value in rgb_triplet)


# Conversions from color names to various formats.
#################################################################


def name_to_hex(name: str, spec: str = CSS3) -> str:
    """
    Convert a color name to a normalized hexadecimal color value.

    The optional keyword argument ``spec`` determines which
    specification's list of color names will be used. The default is
    CSS3.

    When no color of that name exists in the given specification,
    ``ValueError`` is raised.

    """
    if spec not in SUPPORTED_SPECIFICATIONS:
        raise ValueError(SPECIFICATION_ERROR_TEMPLATE.format(spec=spec))
    normalized = name.lower()
    hex_value = {
        CSS2: CSS2_NAMES_TO_HEX,
        CSS21: CSS21_NAMES_TO_HEX,
        CSS3: CSS3_NAMES_TO_HEX,
        HTML4: HTML4_NAMES_TO_HEX,
    }[spec].get(normalized)
    if hex_value is None:
        raise ValueError(
            "'{name}' is not defined as a named color in {spec}".format(
                name=name, spec=spec
            )
        )
    return hex_value


def name_to_rgb(name: str, spec: str = CSS3) -> IntegerRGB:
    """
    Convert a color name to a 3-tuple of integers suitable for use in
    an ``rgb()`` triplet specifying that color.

    """
    return hex_to_rgb(name_to_hex(name, spec=spec))


def name_to_rgb_percent(name: str, spec: str = CSS3) -> PercentRGB:
    """
    Convert a color name to a 3-tuple of percentages suitable for use
    in an ``rgb()`` triplet specifying that color.

    """
    return rgb_to_rgb_percent(name_to_rgb(name, spec=spec))


# Conversions from hexadecimal color values to various formats.
#################################################################


def hex_to_name(hex_value: str, spec: str = CSS3) -> str:
    """
    Convert a hexadecimal color value to its corresponding normalized
    color name, if any such name exists.

    The optional keyword argument ``spec`` determines which
    specification's list of color names will be used. The default is
    CSS3.

    When no color name for the value is found in the given
    specification, ``ValueError`` is raised.

    """
    if spec not in SUPPORTED_SPECIFICATIONS:
        raise ValueError(SPECIFICATION_ERROR_TEMPLATE.format(spec=spec))
    normalized = normalize_hex(hex_value)
    name = {
        CSS2: CSS2_HEX_TO_NAMES,
        CSS21: CSS21_HEX_TO_NAMES,
        CSS3: CSS3_HEX_TO_NAMES,
        HTML4: HTML4_HEX_TO_NAMES,
    }[spec].get(normalized)
    if name is None:
        raise ValueError("'{}' has no defined color name in {}".format(hex_value, spec))
    return name


def hex_to_rgb(hex_value: str) -> IntegerRGB:
    """
    Convert a hexadecimal color value to a 3-tuple of integers
    suitable for use in an ``rgb()`` triplet specifying that color.

    """
    int_value = int(normalize_hex(hex_value)[1:], 16)
    return IntegerRGB(int_value >> 16, int_value >> 8 & 0xFF, int_value & 0xFF)


def hex_to_rgb_percent(hex_value: str) -> PercentRGB:
    """
    Convert a hexadecimal color value to a 3-tuple of percentages
    suitable for use in an ``rgb()`` triplet representing that color.

    """
    return rgb_to_rgb_percent(hex_to_rgb(hex_value))


# Conversions from  integer rgb() triplets to various formats.
#################################################################


def rgb_to_name(rgb_triplet: IntTuple, spec: str = CSS3) -> str:
    """
    Convert a 3-tuple of integers, suitable for use in an ``rgb()``
    color triplet, to its corresponding normalized color name, if any
    such name exists.

    The optional keyword argument ``spec`` determines which
    specification's list of color names will be used. The default is
    CSS3.

    If there is no matching name, ``ValueError`` is raised.

    """
    return hex_to_name(rgb_to_hex(normalize_integer_triplet(rgb_triplet)), spec=spec)


def rgb_to_hex(rgb_triplet: IntTuple) -> str:
    """
    Convert a 3-tuple of integers, suitable for use in an ``rgb()``
    color triplet, to a normalized hexadecimal value for that color.

    """
    return "#{:02x}{:02x}{:02x}".format(*normalize_integer_triplet(rgb_triplet))


def rgb_to_rgb_percent(rgb_triplet: IntTuple) -> PercentRGB:
    """
    Convert a 3-tuple of integers, suitable for use in an ``rgb()``
    color triplet, to a 3-tuple of percentages suitable for use in
    representing that color.

    This function makes some trade-offs in terms of the accuracy of
    the final representation; for some common integer values,
    special-case logic is used to ensure a precise result (e.g.,
    integer 128 will always convert to '50%', integer 32 will always
    convert to '12.5%'), but for all other values a standard Python
    ``float`` is used and rounded to two decimal places, which may
    result in a loss of precision for some values.

    """
    # In order to maintain precision for common values,
    # special-case them.
    specials = {
        255: "100%",
        128: "50%",
        64: "25%",
        32: "12.5%",
        16: "6.25%",
        0: "0%",
    }
    return PercentRGB._make(
        specials.get(d, "{:.02f}%".format(d / 255.0 * 100))
        for d in normalize_integer_triplet(rgb_triplet)
    )


# Conversions from percentage rgb() triplets to various formats.
#################################################################


def rgb_percent_to_name(rgb_percent_triplet: PercentTuple, spec: str = CSS3) -> str:
    """
    Convert a 3-tuple of percentages, suitable for use in an ``rgb()``
    color triplet, to its corresponding normalized color name, if any
    such name exists.

    The optional keyword argument ``spec`` determines which
    specification's list of color names will be used. The default is
    CSS3.

    If there is no matching name, ``ValueError`` is raised.

    """
    return rgb_to_name(
        rgb_percent_to_rgb(normalize_percent_triplet(rgb_percent_triplet)), spec=spec
    )


def rgb_percent_to_hex(rgb_percent_triplet: PercentTuple) -> str:
    """
    Convert a 3-tuple of percentages, suitable for use in an ``rgb()``
    color triplet, to a normalized hexadecimal color value for that
    color.

    """
    return rgb_to_hex(
        rgb_percent_to_rgb(normalize_percent_triplet(rgb_percent_triplet))
    )


def _percent_to_integer(percent: str) -> int:
    """
    Internal helper for converting a percentage value to an integer
    between 0 and 255 inclusive.

    """
    return int(round(float(percent.split("%")[0]) / 100 * 255))


def rgb_percent_to_rgb(rgb_percent_triplet: PercentTuple) -> IntegerRGB:
    """
    Convert a 3-tuple of percentages, suitable for use in an ``rgb()``
    color triplet, to a 3-tuple of integers suitable for use in
    representing that color.

    Some precision may be lost in this conversion. See the note
    regarding precision for ``rgb_to_rgb_percent()`` for details.

    """
    return IntegerRGB._make(
        map(_percent_to_integer, normalize_percent_triplet(rgb_percent_triplet))
    )


# HTML5 color algorithms.
#################################################################

# These functions are written in a way that may seem strange to
# developers familiar with Python, because they do not use the most
# efficient or idiomatic way of accomplishing their tasks. This is
# because, for compliance, these functions are written as literal
# translations into Python of the algorithms in HTML5.
#
# For ease of understanding, the relevant steps of the algorithm from
# the standard are included as comments interspersed in the
# implementation.


def html5_parse_simple_color(input: str) -> HTML5SimpleColor:
    """
    Apply the simple color parsing algorithm from section 2.4.6 of
    HTML5.

    """
    # 1. Let input be the string being parsed.
    #
    # 2. If input is not exactly seven characters long, then return an
    #    error.
    if not isinstance(input, str) or len(input) != 7:
        raise ValueError(
            "An HTML5 simple color must be a Unicode string "
            "exactly seven characters long."
        )

    # 3. If the first character in input is not a U+0023 NUMBER SIGN
    #    character (#), then return an error.
    if not input.startswith("#"):
        raise ValueError(
            "An HTML5 simple color must begin with the " "character '#' (U+0023)."
        )

    # 4. If the last six characters of input are not all ASCII hex
    #    digits, then return an error.
    if not all(c in string.hexdigits for c in input[1:]):
        raise ValueError(
            "An HTML5 simple color must contain exactly six ASCII hex digits."
        )

    # 5. Let result be a simple color.
    #
    # 6. Interpret the second and third characters as a hexadecimal
    #    number and let the result be the red component of result.
    #
    # 7. Interpret the fourth and fifth characters as a hexadecimal
    #    number and let the result be the green component of result.
    #
    # 8. Interpret the sixth and seventh characters as a hexadecimal
    #    number and let the result be the blue component of result.
    #
    # 9. Return result.
    return HTML5SimpleColor(
        int(input[1:3], 16), int(input[3:5], 16), int(input[5:7], 16)
    )


def html5_serialize_simple_color(simple_color: IntTuple) -> str:
    """
    Apply the serialization algorithm for a simple color from section
    2.4.6 of HTML5.

    """
    red, green, blue = simple_color

    # 1. Let result be a string consisting of a single "#" (U+0023)
    #    character.
    result = "#"

    # 2. Convert the red, green, and blue components in turn to
    #    two-digit hexadecimal numbers using lowercase ASCII hex
    #    digits, zero-padding if necessary, and append these numbers
    #    to result, in the order red, green, blue.
    format_string = "{:02x}"
    result += format_string.format(red)
    result += format_string.format(green)
    result += format_string.format(blue)

    # 3. Return result, which will be a valid lowercase simple color.
    return result


def html5_parse_legacy_color(input: str) -> HTML5SimpleColor:
    """
    Apply the legacy color parsing algorithm from section 2.4.6 of
    HTML5.

    """
    # 1. Let input be the string being parsed.
    if not isinstance(input, str):
        raise ValueError(
            "HTML5 legacy color parsing requires a Unicode string as input."
        )

    # 2. If input is the empty string, then return an error.
    if input == "":
        raise ValueError("HTML5 legacy color parsing forbids empty string as a value.")

    # 3. Strip leading and trailing whitespace from input.
    input = input.strip()

    # 4. If input is an ASCII case-insensitive match for the string
    #    "transparent", then return an error.
    if input.lower() == "transparent":
        raise ValueError(
            u'HTML5 legacy color parsing forbids "transparent" as a value.'
        )

    # 5. If input is an ASCII case-insensitive match for one of the
    #    keywords listed in the SVG color keywords section of the CSS3
    #    Color specification, then return the simple color
    #    corresponding to that keyword.
    keyword_hex = CSS3_NAMES_TO_HEX.get(input.lower())
    if keyword_hex is not None:
        return html5_parse_simple_color(keyword_hex)

    # 6. If input is four characters long, and the first character in
    #    input is a "#" (U+0023) character, and the last three
    #    characters of input are all ASCII hex digits, then run these
    #    substeps:
    if (
        len(input) == 4
        and input.startswith("#")
        and all(c in string.hexdigits for c in input[1:])
    ):
        # 1. Let result be a simple color.
        #
        # 2. Interpret the second character of input as a hexadecimal
        #    digit; let the red component of result be the resulting
        #    number multiplied by 17.
        #
        # 3. Interpret the third character of input as a hexadecimal
        #    digit; let the green component of result be the resulting
        #    number multiplied by 17.
        #
        # 4. Interpret the fourth character of input as a hexadecimal
        #    digit; let the blue component of result be the resulting
        #    number multiplied by 17.
        result = HTML5SimpleColor(
            int(input[1], 16) * 17, int(input[2], 16) * 17, int(input[3], 16) * 17
        )

        # 5. Return result.
        return result

    # 7. Replace any characters in input that have a Unicode code
    #    point greater than U+FFFF (i.e. any characters that are not
    #    in the basic multilingual plane) with the two-character
    #    string "00".
    input = "".join("00" if ord(c) > 0xFFFF else c for c in input)

    # 8. If input is longer than 128 characters, truncate input,
    #    leaving only the first 128 characters.
    if len(input) > 128:
        input = input[:128]

    # 9. If the first character in input is a "#" (U+0023) character,
    #    remove it.
    if input.startswith("#"):
        input = input[1:]

    # 10. Replace any character in input that is not an ASCII hex
    #     digit with the character "0" (U+0030).
    input = "".join(c if c in string.hexdigits else "0" for c in input)

    # 11. While input's length is zero or not a multiple of three,
    #     append a "0" (U+0030) character to input.
    while (len(input) == 0) or (len(input) % 3 != 0):
        input += "0"

    # 12. Split input into three strings of equal length, to obtain
    #     three components. Let length be the length of those
    #     components (one third the length of input).
    length = int(len(input) / 3)
    red = input[:length]
    green = input[length : length * 2]
    blue = input[length * 2 :]

    # 13. If length is greater than 8, then remove the leading
    #     length-8 characters in each component, and let length be 8.
    if length > 8:
        red, green, blue = (red[length - 8 :], green[length - 8 :], blue[length - 8 :])
        length = 8

    # 14. While length is greater than two and the first character in
    #     each component is a "0" (U+0030) character, remove that
    #     character and reduce length by one.
    while (length > 2) and (red[0] == "0" and green[0] == "0" and blue[0] == "0"):
        red, green, blue = (red[1:], green[1:], blue[1:])
        length -= 1

    # 15. If length is still greater than two, truncate each
    #     component, leaving only the first two characters in each.
    if length > 2:
        red, green, blue = (red[:2], green[:2], blue[:2])

    # 16. Let result be a simple color.
    #
    # 17. Interpret the first component as a hexadecimal number; let
    #     the red component of result be the resulting number.
    #
    # 18. Interpret the second component as a hexadecimal number; let
    #     the green component of result be the resulting number.
    #
    # 19. Interpret the third component as a hexadecimal number; let
    #     the blue component of result be the resulting number.
    #
    # 20. Return result.
    return HTML5SimpleColor(int(red, 16), int(green, 16), int(blue, 16))
