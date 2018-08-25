from flask_assets import Bundle, Environment, Filter

class ConcatFilter(Filter):
    """
    Filter that merges files, placing a semicolon between them.

    Fixes issues caused by missing semicolons at end of JS assets, for example
    with last statement of jquery.pjax.js.
    """
    def concat(self, out, hunks, **kw):
        out.write(';'.join([h.data() for h, info in hunks]))

css_login = Bundle(
    'node_modules/bootstrap/dist/css/bootstrap.css',
    'node_modules/font-awesome/css/font-awesome.css',
    'node_modules/ionicons/dist/css/ionicons.css',
    'node_modules/icheck/skins/square/blue.css',
    'node_modules/admin-lte/dist/css/AdminLTE.css',
    filters=('cssmin','cssrewrite'),
    output='generated/login.css'
)

js_login = Bundle(
    'node_modules/jquery/dist/jquery.js',
    'node_modules/bootstrap/dist/js/bootstrap.js',
    'node_modules/icheck/icheck.js',
    filters=(ConcatFilter, 'jsmin'),
    output='generated/login.js'
)

js_validation = Bundle(
    'node_modules/bootstrap-validator/dist/validator.js',
    output='generated/validation.js'
)

css_main = Bundle(
    'node_modules/bootstrap/dist/css/bootstrap.css',
    'node_modules/font-awesome/css/font-awesome.css',
    'node_modules/ionicons/dist/css/ionicons.css',
    'node_modules/datatables.net-bs/css/dataTables.bootstrap.css',
    'node_modules/icheck/skins/square/blue.css',
    'node_modules/multiselect/css/multi-select.css',
    'node_modules/admin-lte/dist/css/AdminLTE.css',
    'node_modules/admin-lte/dist/css/skins/_all-skins.css',
    'custom/css/custom.css',
    filters=('cssmin','cssrewrite'),
    output='generated/main.css'
)

js_main = Bundle(
    'node_modules/jquery/dist/jquery.js',
    'node_modules/jquery-ui-dist/jquery-ui.js',
    'node_modules/bootstrap/dist/js/bootstrap.js',
    'node_modules/datatables.net/js/jquery.dataTables.js',
    'node_modules/datatables.net-bs/js/dataTables.bootstrap.js',
    'node_modules/jquery-sparkline/jquery.sparkline.js',
    'node_modules/jquery-slimscroll/jquery.slimscroll.js',
    'node_modules/icheck/icheck.js',
    'node_modules/fastclick/lib/fastclick.js',
    'node_modules/moment/moment.js',
    'node_modules/admin-lte/dist/js/adminlte.js',
    'node_modules/multiselect/js/jquery.multi-select.js',
    'custom/js/custom.js',
    filters=(ConcatFilter, 'jsmin'),
    output='generated/main.js'
)

assets = Environment()
assets.register('js_login', js_login)
assets.register('js_validation', js_validation)
assets.register('css_login', css_login)
assets.register('js_main', js_main)
assets.register('css_main', css_main)
