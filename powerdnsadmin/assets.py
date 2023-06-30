from flask_assets import Bundle, Environment, Filter


class ConcatFilter(Filter):
    """
    Filter that merges files, placing a semicolon between them.
    """
    def concat(self, out, hunks, **kw):
        out.write(';'.join([h.data() for h, info in hunks]))


css_login = Bundle(
    'node_modules/@fortawesome/fontawesome-free/css/all.css',
    'node_modules/icheck/skins/square/blue.css',
    'node_modules/admin-lte/dist/css/adminlte.css',
    filters=('rcssmin', 'cssrewrite'),
    output='generated/login.css')

js_login = Bundle(
    'node_modules/jquery/dist/jquery.js',
    'node_modules/bootstrap/dist/js/bootstrap.js',
    'node_modules/icheck/icheck.js',
    'node_modules/knockout/build/output/knockout-latest.js',
    'custom/js/custom.js',
    filters=(ConcatFilter, 'rjsmin'),
    output='generated/login.js')

js_validation = Bundle(
    'node_modules/bootstrap-validator/dist/validator.js',
    output='generated/validation.js')

css_main = Bundle(
    'node_modules/@fortawesome/fontawesome-free/css/all.css',
    'node_modules/datatables.net-bs4/css/dataTables.bootstrap4.css',
    'node_modules/icheck/skins/square/blue.css',
    'node_modules/multiselect/css/multi-select.css',
    'node_modules/admin-lte/dist/css/adminlte.css',
    'custom/css/custom.css',
    'node_modules/bootstrap-datepicker/dist/css/bootstrap-datepicker.css',
    filters=('rcssmin', 'cssrewrite'),
    output='generated/main.css')

js_main = Bundle(
    'node_modules/jquery/dist/jquery.js',
    'node_modules/jquery-ui-dist/jquery-ui.js',
    'node_modules/bootstrap/dist/js/bootstrap.bundle.js',
    'node_modules/datatables.net/js/jquery.dataTables.js',
    'node_modules/datatables.net-bs4/js/dataTables.bootstrap4.js',
    'node_modules/jquery-sparkline/jquery.sparkline.js',
    'node_modules/jquery-slimscroll/jquery.slimscroll.js',
    'node_modules/jquery-validation/dist/jquery.validate.js',
    'node_modules/icheck/icheck.js',
    'node_modules/fastclick/lib/fastclick.js',
    'node_modules/moment/moment.js',
    'node_modules/admin-lte/dist/js/adminlte.js',
    'node_modules/multiselect/js/jquery.multi-select.js',
    'node_modules/datatables.net-plugins/sorting/natural.js',
    'node_modules/jtimeout/src/jTimeout.js',
    'node_modules/jquery.quicksearch/src/jquery.quicksearch.js',
    'node_modules/knockout/build/output/knockout-latest.js',
    'custom/js/app-authentication-settings-editor.js',
    'custom/js/custom.js',
    'node_modules/bootstrap-datepicker/dist/js/bootstrap-datepicker.js',
    filters=(ConcatFilter, 'rjsmin'),
    output='generated/main.js')

assets = Environment()
assets.register('js_login', js_login)
assets.register('js_validation', js_validation)
assets.register('css_login', css_login)
assets.register('js_main', js_main)
assets.register('css_main', css_main)
