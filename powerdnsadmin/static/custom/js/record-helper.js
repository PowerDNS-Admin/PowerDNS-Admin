(function (global) {
    'use strict';

    function splitRecord(value) {
        var trimmedValue = value.trim();
        return trimmedValue ? trimmedValue.split(/\s+/) : [];
    }

    function removeOuterQuotes(value) {
        if (value.length >= 2 && value.startsWith('"') && value.endsWith('"')) {
            return value.slice(1, -1);
        }
        return value;
    }

    function quote(value) {
        return /^".*"$/.test(value) ? value : '"' + value + '"';
    }

    function appendTrailingDot(value) {
        return value && !value.endsWith('.') ? value + '.' : value;
    }

    function positionalParser(fieldCount, quotedFieldIndex) {
        return function (value) {
            var parts = splitRecord(value);
            var values = [];

            for (var index = 0; index < fieldCount; index += 1) {
                values.push(parts[index] || '');
            }
            if (quotedFieldIndex !== undefined) {
                values[quotedFieldIndex] = removeOuterQuotes(
                    parts.slice(quotedFieldIndex).join(' '));
            }
            return values;
        };
    }

    function serviceBindingParser(value) {
        var match = value.trim().match(/^(\S+)(?:\s+(\S+))?(?:\s+([\s\S]*))?$/);

        return match ? [match[1], match[2] || '', match[3] || ''] : ['', '', ''];
    }

    function normalizeServiceBindingParameters(value) {
        return value.trim().replace(
            /(^|\s)([a-z0-9-]+)="([^"\\\s]*)"(?=\s|$)/gi,
            '$1$2=$3');
    }

    function formatServiceBinding(values) {
        var record = values[0].trim() + ' ' +
            appendTrailingDot(values[1].trim());
        var parameters = normalizeServiceBindingParameters(values[2]);

        return parameters ? record + ' ' + parameters : record;
    }

    var serviceBindingFields = [
        ['SvcPriority', 'eg. 1'],
        ['TargetName', 'eg. svc.example.com'],
        ['SvcParams', 'eg. alpn=h2,h3 port=8443', 'textarea']
    ];

    var definitions = {
        APL: {
            fields: [[
                'Address Prefix List',
                'eg. 1:192.0.2.0/24 !2:2001:db8::/32',
                'textarea'
            ]],
            parse: function (value) {
                return [value];
            },
            format: function (values) {
                return values[0].trim();
            }
        },
        CAA: {
            fields: [
                ['CAA Flag', '0'],
                ['CAA Tag', 'issue'],
                ['CAA Value', 'eg. letsencrypt.org']
            ],
            parse: positionalParser(3, 2),
            format: function (values) {
                return values[0] + ' ' + values[1] + ' ' + quote(values[2]);
            }
        },
        MX: {
            fields: [
                ['MX Priority', 'eg. 10'],
                ['MX Server', 'eg. postfix.example.com']
            ],
            parse: positionalParser(2),
            format: function (values) {
                return appendTrailingDot(values[0] + ' ' + values[1]);
            }
        },
        HTTPS: {
            fields: serviceBindingFields,
            parse: serviceBindingParser,
            format: formatServiceBinding
        },
        SRV: {
            fields: [
                ['SRV Priority', '0'],
                ['SRV Weight', '10'],
                ['SRV Port', '5060'],
                ['SRV Target', 'sip.example.com']
            ],
            parse: positionalParser(4),
            format: function (values) {
                return appendTrailingDot(values.join(' '));
            }
        },
        SVCB: {
            fields: serviceBindingFields,
            parse: serviceBindingParser,
            format: formatServiceBinding
        },
        SOA: {
            fields: [
                ['Primary Name Server', 'ns1.example.com'],
                ['Primary Contact', 'admin.example.com'],
                ['Serial', '2016010101'],
                ['Zone refresh timer', '86400'],
                ['Failed refresh retry timer', '7200'],
                ['Zone expiry timer', '1209600'],
                ['Minimum TTL', '300']
            ],
            parse: positionalParser(7),
            format: function (values) {
                return values.join(' ');
            }
        },
        TLSA: {
            fields: [
                ['TLSA Certificate Usage', '3'],
                ['TLSA Selector', '1'],
                ['TLSA Matching Type', '1'],
                ['Hash', 'HASH']
            ],
            parse: positionalParser(4),
            format: function (values) {
                return values.join(' ');
            }
        },
        TXT: {
            fields: [['TXT Record Data', 'Your TXT record data', 'textarea']],
            parse: function (value) {
                return [removeOuterQuotes(value)];
            },
            format: function (values) {
                return quote(values[0]);
            }
        },
        LUA: {
            fields: [
                ['Lua Record Type', 'Initial query type. Example: A, CNAME or PTR'],
                ['Lua Record Data', 'Your LUA snippet', 'textarea']
            ],
            parse: function (value) {
                var separator = value.indexOf(' ');
                if (separator === -1) {
                    return [value, ''];
                }
                return [
                    value.slice(0, separator),
                    removeOuterQuotes(value.slice(separator + 1))
                ];
            },
            format: function (values) {
                return values[0] + ' ' + quote(values[1]);
            }
        }
    };

    function fieldId(recordType, index) {
        return 'record-helper-' + recordType.toLowerCase() + '-' + index;
    }

    function renderFields(container, recordType, definition, values) {
        container.replaceChildren();

        definition.fields.forEach(function (field, index) {
            var wrapper = document.createElement('div');
            var label = document.createElement('label');
            var control = field[2] === 'textarea'
                ? document.createElement('textarea')
                : document.createElement('input');
            var id = fieldId(recordType, index);

            wrapper.className = 'mb-3';
            label.className = 'form-label';
            label.htmlFor = id;
            label.textContent = field[0];
            control.className = 'form-control';
            control.id = id;
            control.name = id;
            control.placeholder = field[1];
            control.value = values[index] || '';
            if (control.tagName === 'TEXTAREA') {
                control.rows = 5;
            } else {
                control.type = 'text';
            }

            wrapper.append(label, control);
            container.append(wrapper);
        });
    }

    function initializeRecordHelper(options) {
        options = options || {};

        function bindRecordHelper() {
            var modal = document.querySelector(options.modalSelector || '#modal_custom_record');
            var inputSelector = options.inputSelector || '#current_edit_record_data';
            var typeSelector = options.typeSelector || '#record_type';
            var container = modal && modal.querySelector('.custom-record-form');
            var saveButton = modal && modal.querySelector('[data-record-helper-save]');
            var title = modal && modal.querySelector('.modal-title');
            var activeInput = null;
            var activeDefinition = null;

            if (!modal || !container || !saveButton ||
                    document.body.dataset.recordHelperInitialized === 'true') {
                return;
            }
            document.body.dataset.recordHelperInitialized = 'true';

            function openRecordHelper(recordInput) {
                var row = recordInput && recordInput.closest('tr');
                var typeInput = row && row.querySelector(typeSelector);
                var recordType = typeInput && typeInput.value.toUpperCase();
                var definition = definitions[recordType];

                if (!recordInput || !definition) {
                    return;
                }

                activeInput = recordInput;
                activeDefinition = definition;
                title.textContent = recordType + ' Record Helper';
                renderFields(
                    container,
                    recordType,
                    definition,
                    definition.parse(recordInput.value));
                showModal(modal);
            }

            // Opening on focus caused the helper to immediately relaunch when
            // Bootstrap returned focus to the record field after closing the
            // modal. Require an explicit pointer or keyboard action instead.
            document.body.addEventListener('click', function (event) {
                var recordInput = event.target.closest(inputSelector);
                if (recordInput) {
                    openRecordHelper(recordInput);
                }
            });

            document.body.addEventListener('keydown', function (event) {
                var recordInput = event.target.closest(inputSelector);
                if (recordInput && (event.key === 'Enter' || event.key === 'F2')) {
                    event.preventDefault();
                    openRecordHelper(recordInput);
                }
            });

            saveButton.addEventListener('click', function () {
                if (!activeInput || !activeDefinition) {
                    return;
                }

                var values = Array.from(
                    container.querySelectorAll('.form-control'),
                    function (control) { return control.value; });
                activeInput.value = activeDefinition.format(values);
                hideModal(modal);
                activeInput.dispatchEvent(new Event('change', { bubbles: true }));
            });

            modal.addEventListener('hidden.bs.modal', function () {
                activeInput = null;
                activeDefinition = null;
                container.replaceChildren();
            });
        }

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', bindRecordHelper, { once: true });
        } else {
            bindRecordHelper();
        }
    }

    global.initializeRecordHelper = initializeRecordHelper;
}(window));
