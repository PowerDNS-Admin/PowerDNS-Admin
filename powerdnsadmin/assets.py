from flask_assets import Bundle, Environment, Filter


class ConcatFilter(Filter):
    """
    Filter that merges files, placing a semicolon between them.
    """
    def concat(self, out, hunks, **kw):
        out.write(';'.join([h.data() for h, info in hunks]))


css_login = Bundle(
    'node_modules/@fortawesome/fontawesome-free/css/all.css',
    'node_modules/admin-lte/dist/css/adminlte.css',
    filters=('rcssmin', 'cssrewrite'),
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
    filters=('rcssmin', 'cssrewrite'),
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
