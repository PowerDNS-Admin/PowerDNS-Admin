import json
from io import StringIO
from pathlib import Path

from powerdnsadmin.assets import (ModernBrowserCssFilter, css_login, css_main,
                                  js_main)


def test_css_bundles_normalize_vendor_css_for_supported_browsers():
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
    assert isinstance(css_login.filters[0], ModernBrowserCssFilter)
    assert isinstance(css_main.filters[0], ModernBrowserCssFilter)


def test_main_bundle_uses_native_monospace_fonts():
    stylesheet = Path(
        'powerdnsadmin/static/custom/css/custom.css').read_text()

    assert 'ui-monospace' in stylesheet
    assert 'Roboto Mono' not in stylesheet
    assert 'assets/css/roboto_mono.css' not in Path(
        'powerdnsadmin/templates/base.html').read_text()


def test_javascript_dependencies_are_bundled_before_their_extensions():
    sources = list(js_main.contents)

    datatables = sources.index('node_modules/datatables.net/js/jquery.dataTables.js')
    datatables_bootstrap = sources.index(
        'node_modules/datatables.net-bs5/js/dataTables.bootstrap5.js')
    natural_sort = sources.index(
        'node_modules/datatables.net-plugins/sorting/natural.js')
    adminlte = sources.index('node_modules/admin-lte/dist/js/adminlte.js')
    application = sources.index('custom/js/custom.js')
    record_helper = sources.index('custom/js/record-helper.js')

    assert (datatables < datatables_bootstrap < natural_sort < adminlte <
            application < record_helper)


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
        "{% include 'includes/page_header.html' %}",
        '{% block page_header_after %}',
    ):
        assert required_markup in template

    assert 'data-widget=' not in template
    assert 'block dashboard_stat' not in template


def test_theme_is_resolved_before_stylesheets_in_every_document_template():
    template_root = Path('powerdnsadmin/templates')
    theme_include = "{% include 'includes/theme_bootstrap.html' %}"
    document_templates = []

    for path in template_root.rglob('*.html'):
        template = path.read_text()
        if '<!DOCTYPE html>' in template:
            document_templates.append((path, template))

    assert document_templates
    for path, template in document_templates:
        assert theme_include in template, path
        first_stylesheet = template.find('rel="stylesheet"')
        if first_stylesheet != -1:
            assert template.index(theme_include) < first_stylesheet, path


def test_theme_bootstrap_matches_adminlte_color_mode_storage():
    template = Path(
        'powerdnsadmin/templates/includes/theme_bootstrap.html').read_text()

    assert "var storageKey = 'lte-theme';" in template
    assert 'window.localStorage.getItem(storageKey)' in template
    assert 'window.localStorage.setItem(storageKey, theme)' in template
    assert "prefers-color-scheme: dark" in template
    assert "setAttribute('data-bs-theme', resolvedTheme)" in template
    assert 'root.style.colorScheme = resolvedTheme' in template


def test_session_warning_modal_is_bound_after_dom_is_ready():
    template = Path('powerdnsadmin/templates/base.html').read_text()
    ready_handler = template.index('// jTimeout definition')
    modal_lookup = template.index(
        "document.getElementById('modal_session_warning')")
    timeout_initialization = template.index('$.jTimeout({')

    assert ready_handler < modal_lookup < timeout_initialization


def test_dashboard_uses_bootstrap_5_tabs_and_aligned_breadcrumbs():
    template = Path('powerdnsadmin/templates/dashboard.html').read_text()
    domain_row = Path(
        'powerdnsadmin/templates/dashboard_domain.html').read_text()
    custom_javascript = Path(
        'powerdnsadmin/static/custom/js/custom.js').read_text()
    page_header = Path(
        'powerdnsadmin/templates/includes/page_header.html').read_text()

    assert 'data-bs-toggle="pill"' in template
    assert 'data-toggle="pill"' not in template
    assert "{% set page_title = 'Dashboard' %}" in template
    assert 'breadcrumb justify-content-sm-end mb-0' in page_header
    assert 'dropdown dashboard-action-dropdown' in domain_row
    assert 'initializeDashboardDropdownPortals' in custom_javascript
    assert 'document.body.appendChild(menu)' in custom_javascript


def test_dashboard_v2_is_a_parallel_client_rendered_preview():
    classic = Path('powerdnsadmin/templates/dashboard.html').read_text()
    template = Path('powerdnsadmin/templates/dashboard_v2.html').read_text()
    javascript = Path(
        'powerdnsadmin/static/custom/js/dashboard-v2.js').read_text()
    routes = Path('powerdnsadmin/routes/dashboard.py').read_text()

    assert "url_for('dashboard.dashboard_v2')" in classic
    assert "@dashboard_bp.route('/v2/', methods=['GET'])" in routes
    assert "@dashboard_bp.route('/v2/domains/<path:tab_id>'" in routes
    assert "'recordsTotal': total_count" in routes
    assert "'recordsFiltered': filtered_count" in routes
    assert "'permissions': {" in routes
    assert 'Please wait while we load the zone data' in template
    assert 'aria-busy="true"' in template
    assert 'dashboard-table-retry' in template
    assert 'data-dashboard-v2-table' in template
    assert '<tbody></tbody>' in template
    assert '{% for domain in' not in template
    assert 'dashboard-v2-card-header' in template
    assert 'dashboard-v2-tabs' in template
    assert 'Forward Zones' in template
    assert 'Reverse Zones' in template
    assert 'dashboard-v2-forward-option' in template
    assert 'dashboard-v2-reverse-option' in template
    assert '>IPv4<' in template.replace('\n', '').replace(' ', '')
    assert '>IPv6<' in template.replace('\n', '').replace(' ', '')
    assert 'dashboard-v2-table-toolbar' in template
    assert 'dashboard-v2-table-footer' in template
    assert 'td.dataTables_empty' in template
    assert "shown.bs.tab" in javascript
    assert 'serverSide: true' in javascript
    assert 'deferRender: true' in javascript
    assert 'document.createElement' in javascript
    assert '.innerHTML' not in javascript
    assert "'dropdown dashboard-action-dropdown'" in javascript
    assert "document.addEventListener('click'" in javascript
    assert 'id="modal_dnssec_enable_v2"' in template
    assert 'dnssec-enable-v2-keytype' in template
    assert 'dnssec-enable-v2-algorithm' in template
    assert 'dnssec-enable-v2-bits' in template
    assert 'id="modal_dnssec_status_v2"' in template
    assert 'dnssec-status-v2-nameservers' in template
    assert 'id="modal_dnssec_rollover_v2"' in template
    assert 'dnssec-status-v2-start-rollover' in template
    assert 'dnssec-rollover-v2-type' in template
    assert 'button_dnssec_configure' in javascript
    assert 'button_dnssec_status_v2' in javascript
    assert 'dashboard-dnssec-pill' in javascript
    assert "' Signed'" in javascript
    assert "' Unsigned'" in javascript
    assert "'Edit records'" in javascript
    assert "' Manage DNSSEC'" in javascript
    assert 'fa-solid fa-ellipsis' in javascript
    assert "lengthMenu: 'Rows _MENU_'" in javascript
    assert "paginate: {previous: 'Prev', next: 'Next'}" in javascript
    assert 'renderOptionalText' in javascript
    assert 'compactRequestData' in javascript
    assert 'initializeBackgroundTables' in javascript
    assert 'initialLoadComplete' in javascript
    assert 'loadDnssecStatus' in javascript
    assert 'openDnssecRolloverModal' in javascript
    assert 'undelegated' in javascript
    assert 'dnssecStatusV2' in routes
    assert 'dnssec_rollover_create_v2' in routes
    assert "'/dashboard/v2/domains/'" in javascript
    assert "document.addEventListener('DOMContentLoaded', initializeDashboardV2" in javascript


def test_zone_editor_uses_bootstrap_5_utilities_and_modal_api():
    template = Path('powerdnsadmin/templates/domain.html').read_text()

    for legacy_markup in (
        'ml-2',
        'text-right',
        'pull-left',
        'data-dismiss=',
        'data-toggle=',
        'data-target=',
        'class="close"',
        '.modal(',
        'modal.style.display',
    ):
        assert legacy_markup not in template

    assert 'className: "text-end"' in template
    assert template.count('showModal(modal)') == 2
    assert template.count('hideModal(modal)') == 2
    assert "showModal('#WarnLeave')" in template
    assert "hideModal('#WarnLeave')" in template

    for modal_id in (
        'modal_delete',
        'modal_apply_changes',
        'WarnLeave',
    ):
        modal_start = template.index(f'id="{modal_id}"')
        modal_markup = template[modal_start:modal_start + 160]
        assert 'tabindex="-1"' in modal_markup
        assert 'aria-labelledby=' in modal_markup
        assert 'aria-hidden="true"' in modal_markup

    assert 'class="btn-close" data-bs-dismiss="modal"' in template
    assert 'data-bs-dismiss="modal"' in template


def test_zone_editor_binds_unsaved_navigation_and_record_helpers_once():
    template = Path('powerdnsadmin/templates/domain.html').read_text()
    detection_start = template.index('function detectUnsavedChanges(table)')
    warning_start = template.index('function unsavedChangesWarning(', detection_start)
    detection_function = template[detection_start:warning_start]

    assert 'addEventListener' not in detection_function
    assert template.count("document.body.addEventListener('click'") == 1
    assert "event.target.closest('a.nav-link:not(.no-prompt)')" in template


def test_zone_editor_uses_a_persistent_unsaved_changes_banner():
    template = Path('powerdnsadmin/templates/domain.html').read_text()
    stylesheet = Path(
        'powerdnsadmin/static/custom/css/custom.css').read_text()

    assert '{% block page_header_after %}' in template
    assert 'id="unsaved-changes-banner"' in template
    assert 'aria-live="polite"' in template
    assert 'id="apply-unsaved-changes"' in template
    assert 'id="review-unsaved-changes"' in template
    assert "classList.toggle('is-visible', unsavedChanges)" in template
    assert "document.querySelector('.button_apply_changes').click()" in template
    assert "getZoneEditorScrollContainer()" in template
    assert "scrollContainer.scrollTo" in template
    assert "editorHeading.focus({ preventScroll: true })" in template
    assert 'unsaved-changes-card' not in template
    assert '.pda-unsaved-banner {' in stylesheet
    assert '.pda-unsaved-banner.is-floating {' in stylesheet
    assert 'position: fixed;' in stylesheet
    assert '--pda-banner-left' in stylesheet
    assert '.pda-unsaved-banner.is-visible {' in stylesheet
    assert '@media (prefers-reduced-motion: reduce)' in stylesheet


def test_record_helper_is_shared_by_domain_and_template_editors():
    domain = Path('powerdnsadmin/templates/domain.html').read_text()
    template_editor = Path(
        'powerdnsadmin/templates/template_edit.html').read_text()
    modal = Path(
        'powerdnsadmin/templates/includes/record_helper_modal.html').read_text()
    helper = Path(
        'powerdnsadmin/static/custom/js/record-helper.js').read_text()

    for editor in (domain, template_editor):
        assert editor.count('initializeRecordHelper();') == 1
        assert editor.count(
            "{% include 'includes/record_helper_modal.html' %}") == 1
        assert '//handle wacky record types' not in editor
        assert 'caa_flag' not in editor
        assert 'modal_custom_record' not in editor

    for record_type in (
            'APL', 'CAA', 'HTTPS', 'MX', 'SRV', 'SVCB', 'SOA', 'TLSA',
            'TXT', 'LUA'):
        assert f'{record_type}:' in helper

    assert "['SvcPriority', 'eg. 1']" in helper
    assert "['TargetName', 'eg. svc.example.com']" in helper
    assert "['SvcParams', 'eg. alpn=h2,h3 port=8443', 'textarea']" in helper
    assert 'appendTrailingDot(values[1].trim())' in helper
    assert 'normalizeServiceBindingParameters(values[2])' in helper
    assert "'Address Prefix List'" in helper

    assert 'global.initializeRecordHelper = initializeRecordHelper' in helper
    assert 'document.body.dataset.recordHelperInitialized' in helper
    assert "document.body.addEventListener('click'" in helper
    assert "event.key === 'Enter' || event.key === 'F2'" in helper
    assert "document.body.addEventListener('focusin'" not in helper
    assert '.innerHTML' not in helper
    assert 'id="modal_custom_record"' in modal
    assert 'data-record-helper-save' in modal
    assert 'data-bs-dismiss="modal"' in modal


def test_page_header_markup_is_owned_by_the_shared_component():
    template_root = Path('powerdnsadmin/templates')
    page_header = (template_root / 'includes/page_header.html').read_text()
    child_templates = []

    for path in template_root.rglob('*.html'):
        template = path.read_text()
        if 'extends "base.html"' in template:
            child_templates.append((path, template))

    assert child_templates
    assert 'aria-label="Breadcrumb"' in page_header
    assert 'aria-current="page"' in page_header
    assert "url_for('dashboard.dashboard')" in page_header

    for path, template in child_templates:
        assert 'set page_title' in template, path
        assert 'block dashboard_stat' not in template, path
        assert '<ol class="breadcrumb' not in template, path
        assert 'class="content-header"' not in template, path


def test_history_uses_native_date_inputs_without_bootstrap_datepicker():
    template = Path('powerdnsadmin/templates/admin_history.html').read_text()
    asset_sources = (*css_main.contents, *js_main.contents)

    assert 'type="date" id="min"' in template
    assert 'type="date" id="max"' in template
    assert '.datepicker(' not in template
    assert all('bootstrap-datepicker' not in source for source in asset_sources)


def test_legacy_form_control_dependencies_are_removed():
    dependencies = json.loads(Path('package.json').read_text())['dependencies']
    asset_sources = (*css_main.contents, *js_main.contents)
    templates = '\n'.join(
        path.read_text() for path in Path('powerdnsadmin/templates').rglob('*.html')
    )
    custom_javascript = Path(
        'powerdnsadmin/static/custom/js/custom.js').read_text()

    assert {'icheck', 'multiselect', 'jquery.quicksearch'}.isdisjoint(dependencies)
    assert all('icheck' not in source.lower() for source in asset_sources)
    assert all('multiselect' not in source.lower() for source in asset_sources)
    assert all('quicksearch' not in source.lower() for source in asset_sources)
    assert '.iCheck(' not in templates
    assert '.multiSelect(' not in templates
    assert 'initializeDualList' in custom_javascript
