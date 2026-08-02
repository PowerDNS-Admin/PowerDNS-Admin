(function (global, $) {
    'use strict';

    function initializeDashboardV2() {
    var root = document.getElementById('dashboard-v2');
    if (!root || !$ || !$.fn.DataTable) {
        return;
    }

    var tables = new Map();
    var dnssecEnableContext = null;
    var dnssecStatusContext = null;
    var dnssecStatusPollTimer = null;
    var switchingDnssecModal = false;
    var initialTable = root.querySelector(
        '.tab-pane.active [data-dashboard-v2-table]');
    var initialLoadComplete = false;
    var backgroundTablesStarted = false;

    function element(tagName, className, text) {
        var node = document.createElement(tagName);
        if (className) {
            node.className = className;
        }
        if (text !== undefined && text !== null) {
            node.textContent = String(text);
        }
        return node;
    }

    function htmlText(value) {
        return element(
            'span', '', value === null || value === undefined ? '' : value).outerHTML;
    }

    function icon(className) {
        var node = element('i', className);
        node.setAttribute('aria-hidden', 'true');
        return node;
    }

    function appendMenuButton(menu, options) {
        var button = element('button', 'dropdown-item ' + options.className);
        button.type = 'button';
        if (options.id) {
            button.id = options.id;
        }
        if (options.url) {
            button.dataset.url = options.url;
            button.classList.add('dashboard-v2-navigate');
        }
        button.appendChild(icon(options.icon));
        button.appendChild(document.createTextNode(' ' + options.label));
        menu.appendChild(button);
    }

    function renderName(data, type, row) {
        if (type !== 'display') {
            return data;
        }
        var link = element('a');
        link.href = row.urls.records;
        link.appendChild(element('strong', '', data));
        return link.outerHTML;
    }

    function renderDnssec(data, type) {
        if (type !== 'display') {
            return data ? 1 : 0;
        }

        var pill = element(
            'span',
            'badge rounded-pill dashboard-dnssec-pill ' +
                (data ? 'is-signed' : 'is-unsigned'));
        pill.appendChild(element('span', 'dashboard-dnssec-dot'));
        pill.appendChild(document.createTextNode(data ? ' Signed' : ' Unsigned'));
        return pill.outerHTML;
    }

    function renderZoneType(data, type) {
        var value = String(data || '').toLowerCase();
        if (value === 'master') {
            value = 'primary';
        } else if (value === 'slave') {
            value = 'secondary';
        }
        value = value ? value.charAt(0).toUpperCase() + value.slice(1) : '';
        return type === 'display' ? htmlText(value) : value;
    }

    function renderSerial(data, type, row) {
        var value = String(data) === '0' ? row.notifiedSerial : data;
        return type === 'display' ? htmlText(value) : value;
    }

    function renderPrimary(data, type) {
        var value = data;
        if (!value || value === '[]') {
            value = '—';
        } else {
            var matches = Array.from(String(value).matchAll(/'(.+?)'/g));
            if (matches.length) {
                value = matches.map(function (match) { return match[1]; }).join(', ');
            }
        }
        return type === 'display' ? htmlText(value) : value;
    }

    function renderOptionalText(data, type) {
        var value = data || '—';
        return type === 'display' ? htmlText(value) : value;
    }

    function renderActions(data, type, row) {
        if (type !== 'display') {
            return '';
        }

        var wrapper = element(
            'div', 'dashboard-v2-row-actions d-inline-flex align-items-center gap-1');

        var editButton = element(
            'button',
            'btn btn-sm dashboard-v2-edit-button dashboard-v2-navigate');
        editButton.type = 'button';
        editButton.dataset.url = row.urls.records;
        editButton.appendChild(document.createTextNode('Edit records'));
        wrapper.appendChild(editButton);

        var menu = element('div', 'dropdown-menu');

        if (row.permissions.manageZone) {
            appendMenuButton(menu, {
                className: 'btn-danger', icon: 'fa-solid fa-cog',
                label: 'Zone Settings', url: row.urls.settings
            });
        }
        if (row.permissions.manageDnssec) {
            var dnssecButton = element(
                'button',
                'dropdown-item ' +
                    (row.dnssec ? 'button_dnssec_status_v2' : 'button_dnssec_configure'));
            dnssecButton.type = 'button';
            dnssecButton.id = row.name;
            dnssecButton.dataset.domain = row.name;
            if (row.dnssec) {
                dnssecButton.dataset.statusUrl = row.urls.dnssecStatusV2;
            } else {
                dnssecButton.dataset.enableUrl = row.urls.dnssecEnableV2;
            }
            dnssecButton.appendChild(icon(row.dnssec ? 'fa-solid fa-lock' : 'fa-solid fa-lock-open'));
            dnssecButton.appendChild(document.createTextNode(' Manage DNSSEC'));
            menu.appendChild(dnssecButton);
        }
        if (row.permissions.manageZone) {
            appendMenuButton(menu, {
                className: 'btn-success button_template', icon: 'fa-solid fa-clone',
                label: 'Create Template', id: row.name
            });
        }
        if (row.permissions.viewHistory) {
            appendMenuButton(menu, {
                className: 'btn-primary', icon: 'fa-solid fa-history',
                label: 'Zone Changelog', url: row.urls.changelog
            });
        }
        if (row.permissions.removeZone) {
            menu.appendChild(element('div', 'dropdown-divider'));
            appendMenuButton(menu, {
                className: 'btn-secondary text-danger', icon: 'fa-solid fa-trash',
                label: 'Remove Zone', url: row.urls.remove
            });
        }

        if (menu.childElementCount) {
            var dropdown = element('div', 'dropdown dashboard-action-dropdown');
            var toggle = element(
                'button',
                'btn btn-sm dropdown-toggle dashboard-v2-menu-toggle');
            var menuId = 'dropdownMenu-v2-' + row.id;
            toggle.type = 'button';
            toggle.id = menuId;
            toggle.dataset.bsToggle = 'dropdown';
            toggle.setAttribute('aria-haspopup', 'true');
            toggle.setAttribute('aria-expanded', 'false');
            toggle.appendChild(icon('fa-solid fa-ellipsis'));
            dropdown.appendChild(toggle);
            menu.setAttribute('aria-labelledby', menuId);
            dropdown.appendChild(menu);
            wrapper.appendChild(dropdown);
        }

        return wrapper.outerHTML;
    }

    function stateFor(table) {
        return document.getElementById(table.dataset.stateId);
    }

    function showLoading(table) {
        var state = stateFor(table);
        state.classList.remove('d-none');
        state.querySelector('.dashboard-table-loading').classList.remove('d-none');
        state.querySelector('.dashboard-table-error').classList.add('d-none');
        table.setAttribute('aria-busy', 'true');
    }

    function showError(table, xhr) {
        var state = stateFor(table);
        var message = 'The zone data could not be loaded. Please try again.';
        if (xhr && xhr.status === 401) {
            message = 'Your session has expired. Sign in again and retry.';
        } else if (xhr && xhr.status === 403) {
            message = 'You do not have permission to load this zone data.';
        }
        state.querySelector('.dashboard-table-error-message').textContent = message;
        state.querySelector('.dashboard-table-loading').classList.add('d-none');
        state.querySelector('.dashboard-table-error').classList.remove('d-none');
        state.classList.remove('d-none');
        table.classList.add('d-none');
        table.setAttribute('aria-busy', 'false');
    }

    function showTable(table) {
        stateFor(table).classList.add('d-none');
        table.classList.remove('d-none');
        table.setAttribute('aria-busy', 'false');
    }

    function compactRequestData(requestData, includeRefresh) {
        var data = {
            draw: requestData.draw,
            start: requestData.start,
            length: requestData.length,
            'search[value]': requestData.search.value
        };
        requestData.order.forEach(function (order, index) {
            data['order[' + index + '][column]'] = order.column;
            data['order[' + index + '][dir]'] = order.dir;
        });
        if (includeRefresh) {
            data.refresh = '1';
        }
        return data;
    }

    function initializeBackgroundTables() {
        if (backgroundTablesStarted) {
            return;
        }
        backgroundTablesStarted = true;
        root.querySelectorAll('[data-dashboard-v2-table]').forEach(function (table) {
            if (table !== initialTable) {
                initializeTable(table);
            }
        });
    }

    function initializeTable(table) {
        if (tables.has(table)) {
            return tables.get(table);
        }

        var refreshPending = table.dataset.refreshOnLoad === 'true';
        showLoading(table);
        var dataTable = $(table).DataTable({
            paging: true,
            lengthChange: true,
            searching: true,
            ordering: true,
            processing: true,
            serverSide: true,
            deferRender: true,
            info: true,
            autoWidth: false,
            searchDelay: 300,
            pageLength: Number(table.dataset.pageLength),
            lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
            dom: "<'dashboard-v2-table-toolbar d-flex flex-wrap align-items-center " +
                "justify-content-between gap-3'<'dashboard-v2-filter'f>" +
                "<'dashboard-v2-length'l>>" +
                "<'dashboard-v2-table-scroll'tr>" +
                "<'dashboard-v2-table-footer d-flex flex-wrap align-items-center " +
                "justify-content-between gap-3'ip>",
            language: {
                search: '',
                searchPlaceholder: 'Search zones — use ^ and $ for start and end',
                lengthMenu: 'Rows _MENU_',
                paginate: {previous: 'Prev', next: 'Next'},
                processing: '<span class="spinner-border spinner-border-sm" aria-hidden="true"></span> Updating results…'
            },
            infoCallback: function (settings, start, end, max, total) {
                if (!total) {
                    return 'No zones';
                }
                if (start === 1 && end === total) {
                    return 'Showing ' + total + ' of ' + total + ' zones';
                }
                return 'Showing ' + start + '–' + end + ' of ' + total + ' zones';
            },
            initComplete: function () {
                var wrapper = $(table).closest('.dataTables_wrapper');
                wrapper.find('.dataTables_filter input').attr('aria-label', 'Search zones');
                wrapper.find('.dataTables_length select').attr('aria-label', 'Rows per page');
            },
            columns: [
                {data: 'name', render: renderName},
                {data: 'dnssec', render: renderDnssec},
                {data: 'type', render: renderZoneType},
                {data: 'serial', render: renderSerial},
                {data: 'primary', render: renderPrimary},
                {data: 'account', render: renderOptionalText},
                {data: null, render: renderActions, orderable: false, searchable: false}
            ],
            ajax: function (requestData, callback) {
                $.ajax({
                    url: table.dataset.source,
                    method: 'GET',
                    dataType: 'json',
                    data: compactRequestData(requestData, refreshPending)
                }).done(function (response) {
                    refreshPending = false;
                    callback(response);
                    showTable(table);
                }).fail(function (xhr) {
                    callback({
                        draw: requestData.draw,
                        recordsTotal: 0,
                        recordsFiltered: 0,
                        data: []
                    });
                    showError(table, xhr);
                }).always(function () {
                    if (table === initialTable) {
                        initialLoadComplete = true;
                        initializeBackgroundTables();
                    }
                });
            }
        });
        tables.set(table, dataTable);
        return dataTable;
    }

    function updateDnssecKeySizes() {
        var algorithm = document.getElementById('dnssec-enable-v2-algorithm');
        var selected = algorithm.options[algorithm.selectedIndex];
        var bits = JSON.parse(selected.dataset.bits);
        var defaultBits = Number(selected.dataset.defaultBits);
        var size = document.getElementById('dnssec-enable-v2-bits');
        size.replaceChildren();
        bits.forEach(function (value) {
            var option = element('option', '', value + ' bits');
            option.value = String(value);
            option.selected = Number(value) === defaultBits;
            size.appendChild(option);
        });
        size.disabled = bits.length === 1;
    }

    function setDnssecSubmitBusy(isBusy) {
        var submit = document.getElementById('dnssec-enable-v2-submit');
        submit.disabled = isBusy;
        submit.replaceChildren();
        if (isBusy) {
            submit.appendChild(element('span', 'spinner-border spinner-border-sm me-2'));
            submit.appendChild(document.createTextNode('Generating key…'));
        } else {
            submit.appendChild(icon('fa-solid fa-lock'));
            submit.appendChild(document.createTextNode(' Generate key and enable DNSSEC'));
        }
    }

    function openDnssecEnableModal(domain, enableUrl, table) {
        dnssecEnableContext = {
            domain: domain,
            enableUrl: enableUrl,
            table: table
        };
        document.getElementById('dnssec-enable-v2-domain').textContent = domain;
        document.getElementById('dnssec-enable-v2-form').reset();
        document.getElementById('dnssec-enable-v2-error').classList.add('d-none');
        updateDnssecKeySizes();
        setDnssecSubmitBusy(false);
        hideModal('#modal_dnssec_info');
        showModal('#modal_dnssec_enable_v2');
    }

    function appendTableCell(row, value) {
        var cell = element('td');
        if (value instanceof global.Node) {
            cell.appendChild(value);
        } else {
            cell.textContent = value === null || value === undefined ? '' : String(value);
        }
        row.appendChild(cell);
        return cell;
    }

    function statusBadge(success, yesLabel, noLabel) {
        return element(
            'span',
            'badge ' + (success ? 'text-bg-success' : 'text-bg-secondary'),
            success ? yesLabel : noLabel);
    }

    function clearDnssecStatusPoll() {
        if (dnssecStatusPollTimer) {
            global.clearTimeout(dnssecStatusPollTimer);
            dnssecStatusPollTimer = null;
        }
    }

    function setDnssecStatusBusy(isBusy) {
        var refresh = document.getElementById('dnssec-status-v2-refresh');
        refresh.disabled = isBusy;
        refresh.querySelector('i').classList.toggle('fa-spin', isBusy);
        if (isBusy && !dnssecStatusContext.loaded) {
            document.getElementById('dnssec-status-v2-loading').classList.remove('d-none');
            document.getElementById('dnssec-status-v2-content').classList.add('d-none');
        }
    }

    function renderDnssecKeys(keys) {
        var body = document.getElementById('dnssec-status-v2-keys');
        body.replaceChildren();
        if (!keys.length) {
            var emptyRow = element('tr');
            var emptyCell = appendTableCell(emptyRow, 'PowerDNS returned no cryptokeys for this zone.');
            emptyCell.colSpan = 7;
            emptyCell.className = 'text-body-secondary';
            body.appendChild(emptyRow);
            return;
        }

        keys.forEach(function (key) {
            var row = element('tr');
            appendTableCell(row, key.id);
            appendTableCell(row, String(key.keytype || '').toUpperCase());
            appendTableCell(row, key.algorithm || 'Unknown');
            appendTableCell(row, key.bits ? key.bits + ' bits' : 'N/A');
            appendTableCell(row, statusBadge(key.active, 'Active', 'Inactive'));
            appendTableCell(row, statusBadge(key.published, 'Published', 'Unpublished'));
            appendTableCell(row, (key.ds || []).length);
            body.appendChild(row);
        });
    }

    function renderExpectedDs(expectations) {
        var container = document.getElementById('dnssec-status-v2-expected');
        container.replaceChildren();
        if (!expectations.length) {
            container.appendChild(element(
                'div', 'alert alert-secondary mb-0',
                'No active, published KSK or CSK currently provides a DS record.'));
            return;
        }

        expectations.forEach(function (expectation) {
            var card = element('div', 'card card-outline card-secondary mb-2');
            var body = element('div', 'card-body py-2');
            body.appendChild(element(
                'div', 'fw-semibold mb-1',
                'Key ' + expectation.keyId + ' (' +
                String(expectation.keyType).toUpperCase() + ')'));
            body.appendChild(element(
                'div', 'small text-body-secondary mb-2',
                'The registrar only needs to publish one supported digest for this key.'));
            expectation.ds.forEach(function (record) {
                var recordLine = element('div', 'font-monospace small text-break');
                recordLine.appendChild(document.createTextNode(record));
                body.appendChild(recordLine);
            });
            card.appendChild(body);
            container.appendChild(card);
        });
    }

    function renderParentNameservers(delegation) {
        var body = document.getElementById('dnssec-status-v2-nameservers');
        body.replaceChildren();
        document.getElementById('dnssec-status-v2-parent').textContent =
            delegation.parentZone ? 'Parent zone: ' + delegation.parentZone : '';

        if (!delegation.nameservers.length) {
            var emptyRow = element('tr');
            var emptyCell = appendTableCell(
                emptyRow,
                delegation.error || 'No parent authoritative nameservers were available to check.');
            emptyCell.colSpan = 4;
            emptyCell.className = 'text-body-secondary';
            body.appendChild(emptyRow);
            return;
        }

        delegation.nameservers.forEach(function (server) {
            var row = element('tr');
            appendTableCell(row, server.nameserver);
            appendTableCell(row, server.queriedAddress || (server.addresses || []).join(', ') || 'N/A');

            var status;
            if (server.error) {
                status = element('span', 'badge text-bg-danger', 'Check failed');
            } else if (server.delegated === false) {
                status = element('span', 'badge text-bg-secondary', 'Not delegated');
            } else if (server.matches) {
                status = element('span', 'badge text-bg-success', 'DS matched');
            } else {
                status = element('span', 'badge text-bg-warning', 'DS not found');
            }
            appendTableCell(row, status);

            var observed = element('div', 'small');
            if (server.error) {
                observed.classList.add('text-danger');
                observed.textContent = server.error;
            } else if (server.ds.length) {
                server.ds.forEach(function (record) {
                    observed.appendChild(element('div', 'font-monospace text-break', record));
                });
            } else {
                observed.classList.add('text-body-secondary');
                observed.textContent = 'The authoritative answer contained no DS record.';
            }
            appendTableCell(row, observed);
            body.appendChild(row);
        });
    }

    function renderActiveRollover(data) {
        var rolloverCard = document.getElementById('dnssec-status-v2-rollover');
        var startButton = document.getElementById('dnssec-status-v2-start-rollover');
        var cancelButton = document.getElementById('dnssec-status-v2-cancel-rollover');
        if (!data.rollover) {
            rolloverCard.classList.add('d-none');
            startButton.disabled = false;
            startButton.title = '';
            cancelButton.classList.add('d-none');
            cancelButton.dataset.cancelUrl = '';
            return;
        }

        var rollover = data.rollover;
        rolloverCard.classList.remove('d-none');
        document.getElementById('dnssec-status-v2-rollover-type').textContent =
            String(rollover.type).toUpperCase();
        document.getElementById('dnssec-status-v2-rollover-state').textContent =
            String(rollover.state).replaceAll('_', ' ');
        document.getElementById('dnssec-status-v2-rollover-old-keys').textContent =
            rollover.oldKeyIds.join(', ') || 'None';
        document.getElementById('dnssec-status-v2-rollover-new-keys').textContent =
            rollover.newKeyIds.join(', ') || 'None';
        var reconciliationElement = document.getElementById(
            'dnssec-status-v2-rollover-reconciliation');
        var reconciliation = rollover.reconciliation || {};
        if (reconciliation.state === 'ok') {
            var refreshed = (reconciliation.keys || []).filter(function (key) {
                return key.backendIdChanged;
            });
            reconciliationElement.className = 'alert alert-success mb-2';
            reconciliationElement.textContent = refreshed.length
                ? 'Public key identities verified. PowerDNS key locators were refreshed after a backend change.'
                : 'Public key identities verified against PowerDNS.';
        } else {
            var issues = (reconciliation.issues || []).map(function (issue) {
                return issue.message;
            });
            reconciliationElement.className = 'alert alert-danger mb-2';
            reconciliationElement.textContent = issues.join(' ') ||
                'The rollover keys could not be reconciled safely.';
        }
        document.getElementById('dnssec-status-v2-rollover-guidance').textContent =
            rollover.guidance.message;
        startButton.disabled = true;
        startButton.title = 'Finish or cancel the active rollover first.';
        cancelButton.dataset.cancelUrl = rollover.cancelUrl;
        cancelButton.classList.toggle(
            'd-none', !rollover.guidance.cancellationAllowed);
    }

    function renderDnssecStatus(data) {
        if (!dnssecStatusContext) {
            return;
        }
        var delegation = data.delegation;
        var summary = document.getElementById('dnssec-status-v2-summary');
        var stateMessages = {
            propagated: 'The registrar DS is present on every checked parent nameserver.',
            partial: 'The registrar DS is only present on some parent nameservers. Propagation is still in progress.',
            missing: 'No checked parent nameserver currently serves a matching DS record.',
            undelegated: 'This zone is not delegated by its parent. Registrar DS propagation does not apply.',
            not_applicable: 'There is no active, published KSK or CSK to verify at the parent.',
            error: 'The parent delegation could not be verified. Review the nameserver results and retry.'
        };
        var stateClasses = {
            propagated: 'alert-success',
            partial: 'alert-warning',
            missing: 'alert-warning',
            undelegated: 'alert-info',
            not_applicable: 'alert-secondary',
            error: 'alert-danger'
        };
        summary.className = 'alert ' + (stateClasses[delegation.state] || 'alert-secondary');
        summary.textContent = stateMessages[delegation.state] || 'DNSSEC delegation state is unknown.';

        var checkedAt = new Date(delegation.checkedAt);
        document.getElementById('dnssec-status-v2-checked-at').textContent =
            Number.isNaN(checkedAt.getTime()) ? delegation.checkedAt : checkedAt.toLocaleString();
        renderDnssecKeys(data.keys || []);
        renderExpectedDs(delegation.expectedKeys || []);
        renderParentNameservers(delegation);
        renderActiveRollover(data);
        dnssecStatusContext.latestResponse = data;

        document.getElementById('dnssec-status-v2-loading').classList.add('d-none');
        document.getElementById('dnssec-status-v2-error').classList.add('d-none');
        document.getElementById('dnssec-status-v2-content').classList.remove('d-none');
        dnssecStatusContext.loaded = true;

        clearDnssecStatusPoll();
        if (!['propagated', 'not_applicable', 'undelegated'].includes(delegation.state)) {
            dnssecStatusPollTimer = global.setTimeout(loadDnssecStatus, 15000);
        }
    }

    function updateRolloverKeySizes() {
        var algorithm = document.getElementById('dnssec-rollover-v2-algorithm');
        var selected = algorithm.options[algorithm.selectedIndex];
        var bits = JSON.parse(selected.dataset.bits);
        var defaultBits = Number(selected.dataset.defaultBits);
        var size = document.getElementById('dnssec-rollover-v2-bits');
        size.replaceChildren();
        bits.forEach(function (value) {
            var option = element('option', '', value + ' bits');
            option.value = String(value);
            option.selected = Number(value) === defaultBits;
            size.appendChild(option);
        });
        size.disabled = bits.length === 1;
    }

    function updateRolloverType() {
        var type = document.getElementById('dnssec-rollover-v2-type').value;
        document.getElementById('dnssec-rollover-v2-keytype-group').classList.toggle(
            'd-none', type !== 'algorithm');
    }

    function setRolloverSubmitBusy(isBusy) {
        var submit = document.getElementById('dnssec-rollover-v2-submit');
        submit.disabled = isBusy;
        submit.replaceChildren();
        if (isBusy) {
            submit.appendChild(element('span', 'spinner-border spinner-border-sm me-2'));
            submit.appendChild(document.createTextNode('Staging key…'));
        } else {
            submit.appendChild(icon('fa-solid fa-key'));
            submit.appendChild(document.createTextNode(' Stage replacement key'));
        }
    }

    function selectCurrentRolloverDefaults(data) {
        var activeKeys = (data.keys || []).filter(function (key) { return key.active; });
        var preferredKey = activeKeys.find(function (key) { return key.keytype === 'csk'; }) ||
            activeKeys[0];
        if (!preferredKey) {
            return;
        }

        var type = document.getElementById('dnssec-rollover-v2-type');
        if (['csk', 'ksk', 'zsk'].includes(preferredKey.keytype)) {
            type.value = preferredKey.keytype;
            document.getElementById('dnssec-rollover-v2-keytype').value = preferredKey.keytype;
        }
        var algorithmAliases = {
            ECDSAP256SHA256: 'ecdsa256',
            ECDSAP384SHA384: 'ecdsa384',
            ED25519: 'ed25519',
            ED448: 'ed448',
            RSASHA256: 'rsasha256',
            RSASHA512: 'rsasha512'
        };
        var algorithm = algorithmAliases[String(preferredKey.algorithm).toUpperCase()];
        if (algorithm) {
            document.getElementById('dnssec-rollover-v2-algorithm').value = algorithm;
        }
    }

    function openDnssecRolloverModal() {
        if (!dnssecStatusContext || !dnssecStatusContext.latestResponse ||
                dnssecStatusContext.latestResponse.rollover) {
            return;
        }
        var data = dnssecStatusContext.latestResponse;
        document.getElementById('dnssec-rollover-v2-domain').textContent = data.domain;
        document.getElementById('dnssec-rollover-v2-form').reset();
        document.getElementById('dnssec-rollover-v2-error').classList.add('d-none');
        selectCurrentRolloverDefaults(data);
        updateRolloverType();
        updateRolloverKeySizes();
        setRolloverSubmitBusy(false);

        switchingDnssecModal = true;
        var statusModal = document.getElementById('modal_dnssec_status_v2');
        statusModal.addEventListener('hidden.bs.modal', function () {
            showModal('#modal_dnssec_rollover_v2');
            switchingDnssecModal = false;
        }, {once: true});
        hideModal(statusModal);
    }

    function loadDnssecStatus() {
        if (!dnssecStatusContext) {
            return;
        }
        var requestContext = dnssecStatusContext;
        clearDnssecStatusPoll();
        setDnssecStatusBusy(true);
        $.ajax({
            url: dnssecStatusContext.statusUrl,
            method: 'GET',
            dataType: 'json',
            cache: false
        }).done(function (response) {
            if (dnssecStatusContext === requestContext) {
                renderDnssecStatus(response);
            }
        }).fail(function (xhr) {
            var message = 'The DNSSEC status could not be loaded.';
            if (xhr.responseJSON && xhr.responseJSON.msg) {
                message = xhr.responseJSON.msg;
            }
            var error = document.getElementById('dnssec-status-v2-error');
            error.textContent = message;
            error.classList.remove('d-none');
            document.getElementById('dnssec-status-v2-loading').classList.add('d-none');
        }).always(function () {
            setDnssecStatusBusy(false);
        });
    }

    function openDnssecStatusModal(domain, statusUrl) {
        clearDnssecStatusPoll();
        dnssecStatusContext = {
            domain: domain,
            statusUrl: statusUrl,
            loaded: false,
            latestResponse: null
        };
        document.getElementById('dnssec-status-v2-domain').textContent = domain;
        document.getElementById('dnssec-status-v2-error').classList.add('d-none');
        document.getElementById('dnssec-status-v2-content').classList.add('d-none');
        document.getElementById('dnssec-status-v2-loading').classList.remove('d-none');
        hideModal('#modal_dnssec_info');
        showModal('#modal_dnssec_status_v2');
        loadDnssecStatus();
    }

    document.addEventListener('click', function (event) {
        var retry = event.target.closest('.dashboard-table-retry');
        if (retry) {
            var table = retry.closest('.tab-pane').querySelector('[data-dashboard-v2-table]');
            showLoading(table);
            initializeTable(table).ajax.reload();
            return;
        }

        var navigation = event.target.closest('.dashboard-v2-navigate');
        if (navigation) {
            global.location.href = navigation.dataset.url;
            return;
        }

        var dnssecConfigure = event.target.closest('.button_dnssec_configure');
        if (dnssecConfigure) {
            openDnssecEnableModal(
                dnssecConfigure.dataset.domain,
                dnssecConfigure.dataset.enableUrl,
                dnssecConfigure.closest('table'));
            return;
        }

        var dnssecStatus = event.target.closest('.button_dnssec_status_v2');
        if (dnssecStatus) {
            openDnssecStatusModal(
                dnssecStatus.dataset.domain,
                dnssecStatus.dataset.statusUrl);
        }
    });

    document.getElementById('dashboard-v2-tabs').addEventListener('shown.bs.tab', function (event) {
        var pane = document.querySelector(event.target.dataset.bsTarget);
        var table = pane.querySelector('[data-dashboard-v2-table]');
        if (initialLoadComplete || table === initialTable) {
            initializeTable(table).columns.adjust();
        }
    });

    $(document.body).on('click.dashboardV2', '.refresh-bg-button', function () {
        showModal('#modal_bg_reload');
        reload_domains(root.dataset.domainsUpdaterUrl);
    });

    $(document.body).on('click.dashboardV2', '.button_template', function () {
        var modal = $('#modal_template');
        var domain = this.id;
        var body = modal.find('.modal-body p').empty();
        body.append(
            $('<label>').attr('for', 'template_name').text('Template name'),
            $('<input>').attr({
                type: 'text', name: 'template_name', id: 'template_name',
                placeholder: 'Enter a valid template name (required)'
            }).addClass('form-control'),
            $('<label>').attr('for', 'template_description').text('Template description'),
            $('<input>').attr({
                type: 'text', name: 'template_description', id: 'template_description',
                placeholder: 'Enter a template description (optional)'
            }).addClass('form-control')
        );
        modal.find('#button_save').off('click.dashboardV2').on('click.dashboardV2', function () {
            applyChanges({
                _csrf_token: root.dataset.csrfToken,
                name: modal.find('#template_name').val(),
                description: modal.find('#template_description').val(),
                domain: domain
            }, root.dataset.createTemplateUrl, true);
            hideModal(modal);
        });
        showModal(modal);
    });

    $(document.body).on('click.dashboardV2', '.button_dnssec_enable', function () {
        var domain = this.id;
        openDnssecEnableModal(
            domain,
            $SCRIPT_ROOT + '/dashboard/v2/domains/' + encodeURIComponent(domain) + '/dnssec/enable',
            root.querySelector('.tab-pane.active [data-dashboard-v2-table]'));
    });
    $(document.body).on('click.dashboardV2', '.button_dnssec_disable', function () {
        var domain = this.id;
        enable_dns_sec(
            $SCRIPT_ROOT + '/domain/' + encodeURIComponent(domain) + '/dnssec/disable',
            root.dataset.csrfToken);
    });

    document.getElementById('dnssec-enable-v2-algorithm').addEventListener(
        'change', updateDnssecKeySizes);
    document.getElementById('dnssec-rollover-v2-algorithm').addEventListener(
        'change', updateRolloverKeySizes);
    document.getElementById('dnssec-rollover-v2-type').addEventListener(
        'change', updateRolloverType);
    document.getElementById('dnssec-status-v2-refresh').addEventListener(
        'click', loadDnssecStatus);
    document.getElementById('dnssec-status-v2-start-rollover').addEventListener(
        'click', openDnssecRolloverModal);
    document.getElementById('dnssec-status-v2-cancel-rollover').addEventListener(
        'click', function () {
            if (!dnssecStatusContext || !this.dataset.cancelUrl ||
                    !global.confirm('Remove the staged replacement key and cancel this rollover?')) {
                return;
            }
            var button = this;
            button.disabled = true;
            $.ajax({
                url: button.dataset.cancelUrl,
                method: 'POST',
                dataType: 'json',
                data: {_csrf_token: root.dataset.csrfToken}
            }).done(function () {
                loadDnssecStatus();
            }).fail(function (xhr) {
                var message = 'The staged rollover could not be cancelled.';
                if (xhr.responseJSON && xhr.responseJSON.msg) {
                    message = xhr.responseJSON.msg;
                }
                var error = document.getElementById('dnssec-status-v2-error');
                error.textContent = message;
                error.classList.remove('d-none');
            }).always(function () {
                button.disabled = false;
            });
        });
    document.getElementById('modal_dnssec_status_v2').addEventListener(
        'hidden.bs.modal', function () {
            clearDnssecStatusPoll();
            if (!switchingDnssecModal) {
                dnssecStatusContext = null;
            }
        });
    document.getElementById('modal_dnssec_rollover_v2').addEventListener(
        'hidden.bs.modal', function () {
            if (dnssecStatusContext) {
                showModal('#modal_dnssec_status_v2');
                loadDnssecStatus();
            }
        });
    document.getElementById('dnssec-rollover-v2-form').addEventListener(
        'submit', function (event) {
            event.preventDefault();
            if (!dnssecStatusContext || !dnssecStatusContext.latestResponse ||
                    !this.reportValidity()) {
                return;
            }
            var error = document.getElementById('dnssec-rollover-v2-error');
            error.classList.add('d-none');
            setRolloverSubmitBusy(true);
            $.ajax({
                url: dnssecStatusContext.latestResponse.urls.createRollover,
                method: 'POST',
                dataType: 'json',
                data: {
                    _csrf_token: root.dataset.csrfToken,
                    rollover_type: document.getElementById('dnssec-rollover-v2-type').value,
                    keytype: document.getElementById('dnssec-rollover-v2-keytype').value,
                    algorithm: document.getElementById('dnssec-rollover-v2-algorithm').value,
                    bits: document.getElementById('dnssec-rollover-v2-bits').value
                }
            }).done(function () {
                hideModal('#modal_dnssec_rollover_v2');
            }).fail(function (xhr) {
                var message = 'PowerDNS could not stage the replacement key.';
                if (xhr.responseJSON && xhr.responseJSON.msg) {
                    message = xhr.responseJSON.msg;
                }
                error.textContent = message;
                error.classList.remove('d-none');
            }).always(function () {
                setRolloverSubmitBusy(false);
            });
        });
    document.getElementById('dnssec-enable-v2-form').addEventListener('submit', function (event) {
        event.preventDefault();
        if (!dnssecEnableContext || !this.reportValidity()) {
            return;
        }

        var error = document.getElementById('dnssec-enable-v2-error');
        error.classList.add('d-none');
        setDnssecSubmitBusy(true);
        $.ajax({
            url: dnssecEnableContext.enableUrl,
            method: 'POST',
            dataType: 'json',
            data: {
                _csrf_token: root.dataset.csrfToken,
                keytype: document.getElementById('dnssec-enable-v2-keytype').value,
                algorithm: document.getElementById('dnssec-enable-v2-algorithm').value,
                bits: document.getElementById('dnssec-enable-v2-bits').value
            }
        }).done(function () {
            var context = dnssecEnableContext;
            hideModal('#modal_dnssec_enable_v2');
            if (context.table && tables.has(context.table)) {
                tables.get(context.table).ajax.reload(null, false);
            }
            openDnssecStatusModal(
                context.domain,
                $SCRIPT_ROOT + '/dashboard/v2/domains/' +
                    encodeURIComponent(context.domain) + '/dnssec');
        }).fail(function (xhr) {
            var message = 'PowerDNS could not generate the requested DNSSEC key.';
            if (xhr.responseJSON && xhr.responseJSON.msg) {
                message = xhr.responseJSON.msg;
            }
            error.textContent = message;
            error.classList.remove('d-none');
        }).always(function () {
            setDnssecSubmitBusy(false);
        });
    });

    initializeTable(initialTable);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeDashboardV2, {once: true});
    } else {
        initializeDashboardV2();
    }
}(window, window.jQuery));
