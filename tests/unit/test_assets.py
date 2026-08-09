from io import StringIO

from powerdnsadmin.assets import (ConcatFilter, ModernBrowserCssFilter, assets,
                                  css_login, css_main, js_login, js_main)


class Hunk:
    def __init__(self, content):
        self.content = content

    def data(self):
        return self.content


def test_concat_filter_preserves_source_order_and_separates_scripts():
    output = StringIO()
    hunks = [
        (Hunk('window.first = true'), object()),
        (Hunk('window.second = true'), object()),
        (Hunk('window.third = true'), object()),
    ]

    ConcatFilter().concat(output, hunks)

    assert output.getvalue() == (
        'window.first = true;'
        'window.second = true;'
        'window.third = true'
    )


def test_css_filter_removes_only_unsupported_vendor_css():
    source = (
        '@charset "UTF-8";'
        'body{-webkit-text-size-adjust:100%;color:black}'
        '.column-gap-lg-4{-moz-column-gap:1.5rem!important;'
        'column-gap:1.5rem!important}'
        'button::-moz-focus-inner{padding:0}'
        '.form-range::-moz-focus-outer{border:0}'
        '.form-range::-webkit-slider-thumb:active{background:red}'
        '@media (prefers-contrast:high){.btn{outline:1px solid}}'
    )
    output = StringIO()

    ModernBrowserCssFilter().output(StringIO(source), output)

    assert output.getvalue() == (
        'body{color:black}'
        '.column-gap-lg-4{column-gap:1.5rem!important}'
        '@media (prefers-contrast:more){.btn{outline:1px solid}}'
    )


def test_asset_environment_registers_the_application_bundles():
    expected_bundles = {
        'css_login': (css_login, 'generated/login.css'),
        'css_main': (css_main, 'generated/main.css'),
        'js_login': (js_login, 'generated/login.js'),
        'js_main': (js_main, 'generated/main.js'),
    }

    for name, (bundle, output) in expected_bundles.items():
        assert assets[name] is bundle
        assert bundle.output == output

    assert isinstance(css_login.filters[0], ModernBrowserCssFilter)
    assert isinstance(css_main.filters[0], ModernBrowserCssFilter)
    assert isinstance(js_login.filters[0], ConcatFilter)
    assert isinstance(js_main.filters[0], ConcatFilter)
