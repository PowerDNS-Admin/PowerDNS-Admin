var dnssecKeyList = []

function applyChanges(data, url, showResult, refreshPage) {
    $.ajax({
        type : "POST",
        url : url,
        data : JSON.stringify(data),// now data come in this function
        contentType : "application/json; charset=utf-8",
        crossDomain : true,
        dataType : "json",
        success : function(data, status, jqXHR) {
            console.log("Applied changes successfully.")
            if (showResult) {
                var modal = $("#modal_success");
                modal.find('.modal-body p').text("Applied changes successfully");
                modal.modal('show');
            }
            if (refreshPage) {
                location.reload(true);
            }
        },

        error : function(jqXHR, status) {
            // console.log(jqXHR);
            // var modal = $("#modal_error");
            // modal.find('.modal-body p').text(jqXHR["responseText"]);
            // modal.modal('show');
            console.log(jqXHR);
            var modal = $("#modal_error");
            var responseJson = jQuery.parseJSON(jqXHR.responseText);
            modal.find('.modal-body p').text(responseJson['msg']);
            modal.modal('show');
        }
    });
}

function applyRecordChanges(data, domain) {
    $.ajax({
        type : "POST",
        url : $SCRIPT_ROOT + '/domain/' + domain + '/apply',
        data : JSON.stringify(data),// now data come in this function
        contentType : "application/json; charset=utf-8",
        crossDomain : true,
        dataType : "json",
        success : function(data, status, jqXHR) {
            // update Apply button value
            $.getJSON($SCRIPT_ROOT + '/domain/' + domain + '/info', function(data) {
                $(".button_apply_changes").val(data['serial']);
            });

            console.log("Applied changes successfully.")
            var modal = $("#modal_success");
            modal.find('.modal-body p').text("Applied changes successfully");
            modal.modal('show');
        },

        error : function(jqXHR, status) {
            console.log(jqXHR);
            var modal = $("#modal_error");
            var responseJson = jQuery.parseJSON(jqXHR.responseText);
            modal.find('.modal-body p').text(responseJson['msg']);
            modal.modal('show');
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
        record["record_data"] = r[4].trim();
        records.push(record);
    });
    return records
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

    var record = jqInputs[0].value;
    var button_edit = "<button type=\"button\" class=\"btn btn-flat btn-warning button_edit\" id=\"" + record +  "\">Edit&nbsp;<i class=\"fa fa-edit\"></i></button>"
    var button_delete = "<button type=\"button\" class=\"btn btn-flat btn-danger button_delete\" id=\"" + record +  "\">Delete&nbsp;<i class=\"fa fa-trash\"></i></button>"

    oTable.cell(nRow,5).data(button_edit);
    oTable.cell(nRow,6).data(button_delete);

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
    jqTds[5].innerHTML = '<button type="button" class="btn btn-flat btn-primary button_save">Save</button>';
    jqTds[6].innerHTML = '<button type="button" class="btn btn-flat btn-primary button_cancel">Cancel</button>';

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
        modal.modal('hide');
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
              dnssec_footer = '<button type="button" class="btn btn-flat btn-success button_dnssec_enable pull-left" id="'+domain+'">Enable</button><button type="button" class="btn btn-flat btn-default pull-right" data-dismiss="modal">Cancel</button>';
              modal.find('.modal-footer ').html(dnssec_footer);
            }
            else {
                if (parseFloat(PDNS_VERSION) >= 4.1) {
                  dnssec_footer = '<button type="button" class="btn btn-flat btn-danger button_dnssec_disable pull-left" id="'+domain+'">Disable DNSSEC</button><button type="button" class="btn btn-flat btn-default pull-right" data-dismiss="modal">Close</button>';
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
        modal.modal('show');
    });
}

function reload_domains(url) {
  $.getJSON(url, function(data) {
    $('#modal_bg_reload_content').html("<i class=\"fa fa-check\"></i> Finished: " + data['result']['msg']);
  })
}


// pretty JSON
json_library = {
    replacer: function(match, pIndent, pKey, pVal, pEnd) {
        var key = '<span class=json-key>';
        var val = '<span class=json-value>';
        var str = '<span class=json-string>';
        var r = pIndent || '';
        if (pKey){
            r = r + key + pKey.replace(/[": ]/g, '') + '</span>: ';
        }
        if (pVal){
            r = r + (pVal[0] == '"' ? str : val) + pVal + '</span>';
        }
        return r + (pEnd || '');
    },
    prettyPrint: function(obj) {
        obj = obj.replace(/u'/g, "\'").replace(/'/g, "\"").replace(/(False|None)/g, "\"$1\"");
        var jsonData = JSON.parse(obj);
        var jsonLine = /^( *)("[\w]+": )?("[^"]*"|[\w.+-]*)?([,[{])?$/mg;
            return JSON.stringify(jsonData, null, 3)
            .replace(/&/g, '&amp;').replace(/\\"/g, '&quot;')
            .replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(jsonLine, json_library.replacer);
        }
    };
