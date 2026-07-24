import re

from flask_assets import Bundle, Environment, Filter


class ConcatFilter(Filter):
    """
    Filter that merges files, placing a semicolon between them.
    """
    def concat(self, out, hunks, **kw):
        out.write(';'.join([h.data() for h, info in hunks]))


class ModernBrowserCssFilter(Filter):
    """
    Normalize concatenated vendor CSS for the supported browser matrix.

    Upstream stylesheets are valid when loaded separately, but embedded
    ``@charset`` rules become invalid after concatenation. AdminLTE also
    includes declarations and selectors for browser engines that are outside
    our supported matrix or have since been removed from Firefox.
    """
    _charset = re.compile(
        r'@charset\s+(?:"[^"]*"|\'[^\']*\')\s*;',
        re.IGNORECASE,
    )
    _obsolete_declarations = re.compile(
        r'-(?:moz-column-gap|webkit-text-size-adjust)\s*:[^;{}]+;?',
        re.IGNORECASE,
    )
    _obsolete_rules = re.compile(
        r'[^{}]*::-(?:moz-focus-inner|moz-focus-outer|'
        r'webkit-slider-thumb:active)[^{]*\{[^{}]*\}',
        re.IGNORECASE,
    )
    _legacy_contrast = re.compile(
        r'(prefers-contrast\s*:\s*)high\b',
        re.IGNORECASE,
    )

    def output(self, _in, out, **kwargs):
        css = _in.read()
        css = self._charset.sub('', css)
        css = self._obsolete_declarations.sub('', css)
        css = self._obsolete_rules.sub('', css)
        css = self._legacy_contrast.sub(r'\1more', css)
        out.write(css)


css_login = Bundle(
    'node_modules/@fortawesome/fontawesome-free/css/all.css',
    'node_modules/admin-lte/dist/css/adminlte.css',
    filters=(ModernBrowserCssFilter, 'rcssmin', 'cssrewrite'),
    output='generated/login.css')

js_login = Bundle(
    'node_modules/jquery/dist/jquery.js',
    'node_modules/knockout/build/output/knockout-latest.js',
    'node_modules/bootstrap/dist/js/bootstrap.bundle.js',
    'custom/js/custom.js',
    filters=(ConcatFilter, 'rjsmin'),
    output='generated/login.js')

css_main = Bundle(
    'node_modules/@fortawesome/fontawesome-free/css/all.css',
    'node_modules/admin-lte/dist/css/adminlte.css',
    'node_modules/datatables.net-bs5/css/dataTables.bootstrap5.css',
    'custom/css/custom.css',
    filters=(ModernBrowserCssFilter, 'rcssmin', 'cssrewrite'),
    output='generated/main.css')

js_main = Bundle(
    'node_modules/jquery/dist/jquery.js',
    'node_modules/jquery-validation/dist/jquery.validate.js',
    'node_modules/jtimeout/src/jTimeout.js',
    'node_modules/bootstrap/dist/js/bootstrap.bundle.js',
    'node_modules/datatables.net/js/jquery.dataTables.js',
    'node_modules/datatables.net-bs5/js/dataTables.bootstrap5.js',
    'node_modules/datatables.net-plugins/sorting/natural.js',
    'node_modules/admin-lte/dist/js/adminlte.js',
    'node_modules/knockout/build/output/knockout-latest.js',
    'custom/js/app-authentication-settings-editor.js',
    'custom/js/custom.js',
    'custom/js/record-helper.js',
    filters=(ConcatFilter, 'rjsmin'),
    output='generated/main.js')

assets = Environment()
assets.register('js_login', js_login)
assets.register('css_login', css_login)
assets.register('js_main', js_main)
assets.register('css_main', css_main)
