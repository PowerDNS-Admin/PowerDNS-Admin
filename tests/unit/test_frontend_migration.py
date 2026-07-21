from io import StringIO
from pathlib import Path

from powerdnsadmin.assets import (
    RemoveLegacyCssPropertiesFilter,
    css_main,
    js_main,
)


def test_javascript_dependencies_are_bundled_before_their_extensions():
    sources = list(js_main.contents)

    datatables = sources.index('node_modules/datatables.net/js/jquery.dataTables.js')
    datatables_bootstrap = sources.index(
        'node_modules/datatables.net-bs5/js/dataTables.bootstrap5.js')
    natural_sort = sources.index(
        'node_modules/datatables.net-plugins/sorting/natural.js')
    adminlte = sources.index('node_modules/admin-lte/dist/js/adminlte.js')
    application = sources.index('custom/js/custom.js')

    assert datatables < datatables_bootstrap < natural_sort < adminlte < application


def test_base_template_uses_adminlte_4_layout_and_treeview():
    template = Path('powerdnsadmin/templates/base.html').read_text()

    for required_markup in (
        'class="app-wrapper"',
        'class="app-header navbar',
        'class="app-sidebar ',
        'class="app-main"',
        'class="app-content"',
        'class="app-footer"',
        'data-lte-toggle="sidebar"',
        'data-lte-toggle="treeview"',
    ):
        assert required_markup in template

    assert 'data-widget=' not in template


def test_dashboard_uses_bootstrap_5_tabs_and_aligned_breadcrumbs():
    template = Path('powerdnsadmin/templates/dashboard.html').read_text()

    assert 'data-bs-toggle="pill"' in template
    assert 'data-toggle="pill"' not in template
    assert 'breadcrumb justify-content-sm-end mb-0' in template


def test_history_uses_native_date_inputs_without_bootstrap_datepicker():
    template = Path('powerdnsadmin/templates/admin_history.html').read_text()
    asset_sources = (*css_main.contents, *js_main.contents)

    assert 'type="date" id="min"' in template
    assert 'type="date" id="max"' in template
    assert '.datepicker(' not in template
    assert all('bootstrap-datepicker' not in source for source in asset_sources)


def test_css_bundle_filter_removes_obsolete_mozilla_border_radius():
    source = StringIO(
        '.range{-moz-border-radius:3px;border-radius:3px}'
        '.control{color:red;-moz-border-radius:4px;border-radius:4px}'
    )
    output = StringIO()

    RemoveLegacyCssPropertiesFilter().input(source, output)

    compiled = output.getvalue()
    assert '-moz-border-radius' not in compiled
    assert compiled.count('border-radius') == 2
