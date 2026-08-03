var dnssecKeyList = []

function formatUtcDateTimeLocal(value) {
    if (!value) {
        return value;
    }

    var normalized = String(value).trim().replace(' ', 'T');
    if (!/(Z|[+-]\d{2}:?\d{2})$/i.test(normalized)) {
        normalized += 'Z';
    }

    var date = new Date(normalized);
    if (Number.isNaN(date.getTime())) {
        return value;
    }

    var pad = function (part) {
        return String(part).padStart(2, '0');
    };

    return date.getFullYear() + '-' +
        pad(date.getMonth() + 1) + '-' +
        pad(date.getDate()) + ' ' +
        pad(date.getHours()) + ':' +
        pad(date.getMinutes()) + ':' +
        pad(date.getSeconds());
}

// Baseline options shared by every DataTable on the site. Page-specific
// options (columnDefs, lengthMenu, ajax, etc.) are merged on top per table.
var DATATABLE_DEFAULTS = {
    "paging": true,
    "lengthChange": true,
    "searching": true,
    "ordering": true,
    "info": true,
    "autoWidth": false
};

function initDataTable(selector, options) {
    return $(selector).DataTable($.extend(true, {}, DATATABLE_DEFAULTS, options || {}));
}

// Responsive table containers clip absolutely positioned dropdown menus. Move
// dashboard action menus to the document while they are open so Popper can
// position them against the viewport, then restore their original DOM position.
var dashboardDropdownPortals = new WeakMap();

function initializeDashboardDropdownPortals() {
    document.addEventListener('show.bs.dropdown', function (event) {
        var toggle = event.target;
        var dropdown = toggle.closest('.dashboard-action-dropdown');
        if (!dropdown || dashboardDropdownPortals.has(toggle)) {
            return;
        }

        var menu = dropdown.querySelector(':scope > .dropdown-menu');
        if (!menu) {
            return;
        }

        dashboardDropdownPortals.set(toggle, {
            menu: menu,
            parent: menu.parentNode,
            nextSibling: menu.nextSibling
        });
        document.body.appendChild(menu);
    });

    document.addEventListener('shown.bs.dropdown', function (event) {
        if (!dashboardDropdownPortals.has(event.target)) {
            return;
        }

        var dropdown = bootstrap.Dropdown.getInstance(event.target);
        if (dropdown) {
            dropdown.update();
        }
    });

    document.addEventListener('hidden.bs.dropdown', function (event) {
        var portal = dashboardDropdownPortals.get(event.target);
        if (!portal) {
            return;
        }

        portal.parent.insertBefore(portal.menu, portal.nextSibling);
        dashboardDropdownPortals.delete(event.target);
    });
}

function initializeNativeValidation() {
    document.querySelectorAll('form.needs-validation').forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

document.addEventListener('DOMContentLoaded', initializeNativeValidation);
document.addEventListener('DOMContentLoaded', initializeDashboardDropdownPortals);

function getModalElement(target) {
    if (typeof target === 'string') {
        return document.querySelector(target);
    }
    if (target && target.jquery) {
        return target.get(0);
    }
    return target;
}

function getModal(target) {
    var element = getModalElement(target);
    return element ? bootstrap.Modal.getOrCreateInstance(element) : null;
}

function showModal(target) {
    var modal = getModal(target);
    if (modal) {
        modal.show();
    }
}

function hideModal(target) {
    var modal = getModal(target);
    if (modal) {
        modal.hide();
    }
}

function showMessageModal(target, message) {
    var element = getModalElement(target);
    if (!element) {
        return;
    }
    var messageElement = element.querySelector('.modal-body p');
    if (messageElement) {
        messageElement.textContent = message;
    }
    showModal(element);
}

function showErrorModal(message) {
    showMessageModal('#modal_error', message);
}

function showSuccessModal(message) {
    showMessageModal('#modal_success', message);
}

function getFormControlElement(target) {
    return typeof target === 'string' ? document.querySelector(target) : target;
}

function initializeDualList(target, options) {
    var source = getFormControlElement(target);
    if (!source || source.dataset.pdaDualListInitialized === 'true') {
        return;
    }

    options = options || {};
    var itemName = options.itemName || 'items';
    var wrapper = document.createElement('div');
    var availableList = document.createElement('select');
    var selectedList = document.createElement('select');
    var availableSearch = document.createElement('input');
    var selectedSearch = document.createElement('input');

    wrapper.className = 'pda-dual-list row g-2 align-items-center';
    availableList.className = 'form-select pda-dual-list-options';
    selectedList.className = 'form-select pda-dual-list-options';
    availableList.multiple = true;
    selectedList.multiple = true;
    availableList.setAttribute('aria-label', 'Available ' + itemName);
    selectedList.setAttribute('aria-label', 'Selected ' + itemName);

    [availableSearch, selectedSearch].forEach(function (input) {
        input.type = 'search';
        input.className = 'form-control form-control-sm mb-2';
        input.autocomplete = 'off';
    });
    availableSearch.placeholder = 'Filter available ' + itemName;
    selectedSearch.placeholder = 'Filter selected ' + itemName;

    function createColumn(title, search, list) {
        var column = document.createElement('div');
        var label = document.createElement('label');
        column.className = 'col-12 col-md-5';
        label.className = 'form-label fw-semibold';
        label.textContent = title;
        column.appendChild(label);
        column.appendChild(search);
        column.appendChild(list);
        return column;
    }

    function createButton(label, title, handler) {
        var button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn btn-outline-secondary btn-sm';
        button.textContent = label;
        button.title = title;
        button.setAttribute('aria-label', title);
        button.addEventListener('click', handler);
        return button;
    }

    function visibleSourceOptions(selected, query) {
        var normalizedQuery = query.trim().toLocaleLowerCase();
        return Array.from(source.options).filter(function (option) {
            return option.selected === selected &&
                (!normalizedQuery || option.text.toLocaleLowerCase().includes(normalizedQuery));
        });
    }

    function copyOption(option) {
        var copy = new Option(option.text, option.value);
        copy.disabled = option.disabled;
        copy.style.cssText = option.style.cssText;
        copy.title = option.title;
        return copy;
    }

    function replaceListOptions(list, optionsToRender) {
        list.replaceChildren();
        optionsToRender.forEach(function (option) {
            list.appendChild(copyOption(option));
        });
    }

    function render() {
        replaceListOptions(
            availableList,
            visibleSourceOptions(false, availableSearch.value)
        );
        replaceListOptions(
            selectedList,
            visibleSourceOptions(true, selectedSearch.value)
        );
    }

    function notifyChange() {
        source.dispatchEvent(new Event('change', {bubbles: true}));
    }

    function setSelection(list, selected) {
        var values = new Set(Array.from(list.selectedOptions).map(function (option) {
            return option.value;
        }));
        Array.from(source.options).forEach(function (option) {
            if (values.has(option.value) && !option.disabled) {
                option.selected = selected;
            }
        });
        notifyChange();
        render();
    }

    function setVisibleSelection(selected) {
        var search = selected ? selectedSearch.value : availableSearch.value;
        visibleSourceOptions(selected, search).forEach(function (option) {
            if (!option.disabled) {
                option.selected = !selected;
            }
        });
        notifyChange();
        render();
    }

    var controls = document.createElement('div');
    controls.className = 'col-12 col-md-2 d-grid gap-2 pda-dual-list-controls';
    controls.appendChild(createButton('›', 'Add selected ' + itemName, function () {
        setSelection(availableList, true);
    }));
    controls.appendChild(createButton('»', 'Add all visible ' + itemName, function () {
        setVisibleSelection(false);
    }));
    controls.appendChild(createButton('‹', 'Remove selected ' + itemName, function () {
        setSelection(selectedList, false);
    }));
    controls.appendChild(createButton('«', 'Remove all visible ' + itemName, function () {
        setVisibleSelection(true);
    }));

    wrapper.appendChild(createColumn('Available', availableSearch, availableList));
    wrapper.appendChild(controls);
    wrapper.appendChild(createColumn('Selected', selectedSearch, selectedList));

    availableSearch.addEventListener('input', render);
    selectedSearch.addEventListener('input', render);
    availableList.addEventListener('dblclick', function () {
        setSelection(availableList, true);
    });
    selectedList.addEventListener('dblclick', function () {
        setSelection(selectedList, false);
    });

    source.classList.add('d-none');
    source.dataset.pdaDualListInitialized = 'true';
    source.insertAdjacentElement('afterend', wrapper);
    source.pdaDualList = {render: render};
    render();
}

function clearDualListSelection(target) {
    var source = getFormControlElement(target);
    if (!source) {
        return;
    }
    Array.from(source.options).forEach(function (option) {
        option.selected = false;
    });
    source.dispatchEvent(new Event('change', {bubbles: true}));
    if (source.pdaDualList) {
        source.pdaDualList.render();
    }
}

function applyChanges(data, url, showResult, refreshPage) {
    $.ajax({
        type : "POST",
        url : url,
        data : JSON.stringify(data),// now data come in this function
        contentType : "application/json; charset=utf-8",
        crossDomain : true,
        dataType : "json",
        success : function(data, status, jqXHR) {
            console.log("Applied changes successfully.");
            console.log(data);
            if (showResult) {
                showSuccessModal(data['msg'] || "Applied changes successfully");
            }
            if (refreshPage) {
                location.reload(true);
            }
        },

        error : function(jqXHR, status) {
            console.log(jqXHR);
            var responseJson = jQuery.parseJSON(jqXHR.responseText);
            showErrorModal(responseJson['msg']);
        }
    });
}

function applyRecordChanges(data, domain) {
    $.ajax({
        type : "POST",
        url : $SCRIPT_ROOT + '/domain/' + encodeURIComponent(domain) + '/apply',
        data : JSON.stringify(data),// now data come in this function
        contentType : "application/json; charset=utf-8",
        crossDomain : true,
        dataType : "json",
        success : function(data, status, jqXHR) {
            // update Apply button value
            $.getJSON($SCRIPT_ROOT + '/domain/' + encodeURIComponent(domain) + '/info', function(data) {
                $(".button_apply_changes").val(data['serial']);
            });

            console.log("Applied changes successfully.")
            showSuccessModal("Applied changes successfully");
            setTimeout(() => {window.location.reload()}, 2000);
        },

        error : function(jqXHR, status) {
            console.log(jqXHR);
            var responseJson = jQuery.parseJSON(jqXHR.responseText);
            showErrorModal(responseJson['msg']);
        }
    });
}

function getTableData(table) {
    // reformat - pretty format
    var records = []
    table.rows().every(function() {
        var r = this.data();
        var record = {}
        record["record_name"] = r[0].trim();
        record["record_type"] = r[1].trim();
        record["record_status"] = r[2].trim();
        record["record_ttl"] = r[3].trim();
        record["record_data"] = convertHTMLEntityToText(r[4].trim());
        record["record_comment"] = convertHTMLEntityToText(r[5].trim());
        records.push(record);
    });
    return records
}

function convertHTMLEntityToText(htmlEntity) {
    return $('<textarea />').html(htmlEntity).text();
}

function saveRow(oTable, nRow) {

    var status = 'Disabled';
    var jqInputs = $(oTable.row(nRow).node()).find("input");
    var jqSelect = $(oTable.row(nRow).node()).find("select");

    if (jqSelect[1].value == 'false') {
        status = 'Active';
    }

    oTable.cell(nRow,0).data(jqInputs[0].value);
    oTable.cell(nRow,1).data(jqSelect[0].value);
    oTable.cell(nRow,2).data(status);
    oTable.cell(nRow,3).data(jqSelect[2].value);
    oTable.cell(nRow,4).data(jqInputs[1].value);
    oTable.cell(nRow,5).data(jqInputs[2].value);

    var record = jqInputs[0].value;
    var button_edit = "<button type=\"button\" class=\"btn btn-warning button_edit\" id=\"" + record +  "\">Edit&nbsp;<i class=\"fa fa-edit\"></i></button>"
    var button_delete = "<button type=\"button\" class=\"btn btn-danger button_delete\" id=\"" + record +  "\">Delete&nbsp;<i class=\"fa fa-trash\"></i></button>"

    oTable.cell(nRow,6).data(button_edit);
    oTable.cell(nRow,7).data(button_delete);

    oTable.draw();
}

function restoreRow(oTable, nRow) {
    var aData = oTable.row(nRow).data();
    oTable.row(nRow).data(aData);
    oTable.draw();
}

function sec2str(t){
    var d = Math.floor(t/86400),
        h = Math.floor(t/3600) % 24,
        m = Math.floor(t/60) % 60,
        s = t % 60;
    return (d>0?d+' days ':'')+(h>0?h+' hours ':'')+(m>0?m+' minutes ':'')+(s>0?s+' seconds':'');
}

function editRow(oTable, nRow) {
    var isDisabled = 'true';
    var aData = oTable.row(nRow).data();
    var jqTds = oTable.cells(nRow,'').nodes();
    var record_types = "";
    var ttl_opts = "";
    var ttl_not_found = true;
    for(var i = 0; i < records_allow_edit.length; i++) {
        var record_type = records_allow_edit[i];
        record_types += "<option value=\"" + record_type + "\">" + record_type + "</option>";
    }
    for(var i = 0; i < ttl_options.length; i++) {
        ttl_opts += "<option value=\"" + ttl_options[i][0] + "\">" + ttl_options[i][1] + "</option>";
        if (ttl_options[i][0] == aData[3]) {
          ttl_not_found = false;
        }
    }
    if (ttl_not_found) {
      ttl_opts += "<option value=\"" + aData[3] + "\">" + sec2str(aData[3]) + "</option>";
    }
    jqTds[0].innerHTML = '<input type="text" id="edit-row-focus" class="form-control input-small" value="' + aData[0] + '">';
    jqTds[1].innerHTML = '<select class="form-control" id="record_type" name="record_type" value="' + aData[1]  + '">' + record_types + '</select>';
    jqTds[2].innerHTML = '<select class="form-control" id="record_status" name="record_status" value="' + aData[2]  + '"><option value="false">Active</option><option value="true">Disabled</option></select>';
    jqTds[3].innerHTML = '<select class="form-control" id="record_ttl" name="record_ttl" value="' + aData[3]  + '">' + ttl_opts + '</select>';
    jqTds[4].innerHTML = '<input type="text" style="display:table-cell; width:100% !important" id="current_edit_record_data" name="current_edit_record_data" class="form-control input-small advance-data" value="' + aData[4].replace(/\"/g,"&quot;") + '">';
    jqTds[5].innerHTML = '<input type="text" style="display:table-cell; width:100% !important" id="record_comment" name="record_comment" class="form-control input-small advance-data" value="' + aData[5].replace(/\"/g, "&quot;") + '">';
    jqTds[6].innerHTML = '<button type="button" class="btn btn-primary button_save">Save</button>';
    jqTds[7].innerHTML = '<button type="button" class="btn btn-primary button_cancel">Cancel</button>';

    // set current value of dropdown column
    if (aData[2] == 'Active'){
        isDisabled = 'false';
    }

    SelectElement('record_type', aData[1]);
    SelectElement('record_status', isDisabled);
    SelectElement('record_ttl', aData[3]);
}

function SelectElement(elementID, valueToSelect)
{
    var element = document.getElementById(elementID);
    element.value = valueToSelect;
}

function enable_dns_sec(url, csrf_token) {
  $.post(url, {'_csrf_token': csrf_token}, function(data) {
      var modal = $("#modal_dnssec_info");

      if (data['status'] == 'error'){
          modal.find('.modal-body p').text(data['msg']);
      }
      else {
        hideModal(modal);
        //location.reload();
        window.location.reload(true);
      }
  }, 'json')
}

function getdnssec(url, domain){

    $.getJSON(url, function(data) {
        var dnssec_footer = '';
        var modal = $("#modal_dnssec_info");

        if (data['status'] == 'error'){
            modal.find('.modal-body p').text(data['msg']);
        }
        else {
            var dnssec_msg = '';
            var dnssec = data['dnssec'];

            if (dnssec.length == 0 && parseFloat(PDNS_VERSION) >= 4.1) {
              dnssec_msg = '<h3>DNSSEC is disabled. Click on Enable to activate it.';
              modal.find('.modal-body p').html(dnssec_msg);
              dnssec_footer = '<button type="button" class="btn btn-success button_dnssec_enable float-start" id="'+domain+'">Enable</button><button type="button" class="btn btn-secondary float-end" data-bs-dismiss="modal">Cancel</button>';
              modal.find('.modal-footer ').html(dnssec_footer);
            }
            else {
                if (parseFloat(PDNS_VERSION) >= 4.1) {
                  dnssec_footer = '<button type="button" class="btn btn-danger button_dnssec_disable float-start" id="'+domain+'">Disable DNSSEC</button><button type="button" class="btn btn-secondary float-end" data-bs-dismiss="modal">Close</button>';
                  modal.find('.modal-footer ').html(dnssec_footer);
                }
                for (var i = 0; i < dnssec.length; i++) {
                  if (dnssec[i]['active']){
                      dnssec_msg += '<form>'+
                      '<h3><strong>'+dnssec[i]['keytype']+'</strong></h3>'+
                      '<strong>DNSKEY</strong>'+
                      '<input class="form-control" autocomplete="off" type="text" readonly="true" value="'+dnssec[i]['dnskey']+'">'+
                      '</form>'+
                      '<br/>';
                      if(dnssec[i]['ds']){
                          var dsList = dnssec[i]['ds'];
                          dnssec_msg += '<strong>DS</strong>';
                          for (var j = 0; j < dsList.length; j++){
                              dnssec_msg += '<input class="form-control" autocomplete="off" type="text" readonly="true" value="'+dsList[j]+'">';
                          }
                      }
                      dnssec_msg += '</form>';
                  }
              }
            }
            modal.find('.modal-body p').html(dnssec_msg);
        }
        showModal(modal);
    });
}

function reload_domains(url) {
  $.getJSON(url, function(data) {
    $('#modal_bg_reload_content').html("<i class=\"fa fa-check\"></i> Finished: " + data['result']['msg']);
  })
}


// pretty JSON
json_library = {
    replacer: function (match, pIndent, pKey, pVal, pEnd) {
        var key = '<span class=json-key>';
        var val = '<span class=json-value>';
        var str = '<span class=json-string>';
        var r = pIndent || '';
        if (pKey) {
            // r = r + key + pKey.replace(/[": ]/g, '') + '</span>: ';
            // Keep the quote in the key
            r = r + key + pKey.replace(/":/, '"') + '</span>: ';
        }
        if (pVal) {
            r = r + (pVal[0] == '"' ? str : val) + pVal + '</span>';
        }
        return r + (pEnd || '');
    },
    prettyPrint: function (obj) {
        obj = obj.replace(/u'/g, "\'").replace(/'/g, "\"").replace(/(False|None)/g, "\"$1\"");
        var jsonData = JSON.parse(obj);
        // var jsonLine = /^( *)("[\w]+": )?("[^"]*"|[\w.+-]*)?([,[{])?$/mg;
        // The new regex to handle case value is an empty list [] or dict {}
        var jsonLine = /^( *)("[\w]+": )?("[^"]*"|[\w.+-]*)?([,[{])?/mg;
        return JSON.stringify(jsonData, null, 3)
            .replace(/&/g, '&amp;').replace(/\\"/g, '&quot;')
            .replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(jsonLine, json_library.replacer);
    }
};

// set count down in second on an element
function timer(elToUpdate, maxTime) {
    elToUpdate.text(maxTime + "s");

    var interval = setInterval(function () {
        if (maxTime > 0) {
            maxTime--;
            elToUpdate.text(maxTime + "s");
        }
        else {
            clearInterval(interval);
        }
    }, 1000);

    return interval;
}

// copy otp secret code to clipboard
function copy_otp_secret_to_clipboard() {
    var copyBox = document.getElementById("otp_secret");
    copyBox.select();
    copyBox.setSelectionRange(0, 99999); /* For mobile devices */
    navigator.clipboard.writeText(copyBox.value);
    $("#copy_tooltip").css("visibility", "visible");
    setTimeout(function(){ $("#copy_tooltip").css("visibility", "hidden"); }, 2000);
  }

// Side menu nav bar active selection
/** add active class and stay opened when selected */

// for sidebar menu entirely but not cover treeview
$('ul.sidebar-menu a').filter(function() {
    return this.href == window.location.href.split('?')[0];
}).addClass('active');

// for treeview
$('ul.nav-treeview a').filter(function() {
    return this.href == window.location.href.split('?')[0];
}).parentsUntil(".sidebar-menu > .nav-treeview").addClass('menu-open').prev('a').addClass('active');
