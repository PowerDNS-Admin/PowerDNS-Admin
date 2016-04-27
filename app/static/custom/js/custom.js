function applyChanges(data, url, showResult) {
	var success = false;
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
		},

		error : function(jqXHR, status) {
			console.log(jqXHR);
			var modal = $("#modal_error");
			modal.find('.modal-body p').text(jqXHR["responseText"]);
			modal.modal('show');
		}
	});

}

function getTableData(table) {
	var rData = []

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
	
	var jqInputs = $(oTable.row(nRow).node()).find("input");
	var jqSelect = $(oTable.row(nRow).node()).find("select");

	if (jqSelect[1].value == 'false') {
		status = 'Active';
	} else {
		status = 'Disabled';
	}


	oTable.cell(nRow,0).data(jqInputs[0].value);
	oTable.cell(nRow,1).data(jqSelect[0].value);
	oTable.cell(nRow,2).data(status);
	oTable.cell(nRow,3).data(jqSelect[2].value);
	oTable.cell(nRow,4).data(jqInputs[1].value);

	var record = jqInputs[0].value;
	var button_edit = "<button type=\"button\" class=\"btn btn-flat btn-warning button_edit\" id=\"" + record +  "\">Edit&nbsp;<i class=\"fa fa-edit\"></i></button>"
	var button_delete = "<button type=\"button\" class=\"btn btn-flat btn-danger button_edit\" id=\"" + record +  "\">Delete&nbsp;<i class=\"fa fa-trash\"></i></button>"

	oTable.cell(nRow,5).data(button_edit);
	oTable.cell(nRow,6).data(button_delete);
	
	oTable.draw();
}

function restoreRow(oTable, nRow) {
    var aData = oTable.row(nRow).data();
    var jqTds = $('>td', nRow);
	oTable.row(nRow).data(aData);
	oTable.draw();
}

function editRow(oTable, nRow) {
    var aData = oTable.row(nRow).data();
    var jqTds = oTable.cells(nRow,'').nodes();
    var record_types = "";
    for(var i = 0; i < records_allow_edit.length; i++) {
       var record_type = records_allow_edit[i];
       record_types += "<option value=\"" + record_type + "\">" + record_type + "</option>";
    }
    jqTds[0].innerHTML = '<input type="text" class="form-control input-small" value="' + aData[0] + '">';
    //jqTds[1].innerHTML = '<select class="form-control" id="record_type" name="record_type" value="' + aData[1]  + '"' + '><option value="A">A</option><option value="AAAA">AAAA</option><option value="NS">NS</option><option value="CNAME">CNAME</option><option value="DNAME">DNAME</option><option value="MR">MR</option><option value="PTR">PTR</option><option value="HINFO">HINFO</option><option value="MX">MX</option><option value="TXT">TXT</option><option value="RP">RP</option><option value="AFSDB">AFSDB</option><option value="SIG">SIG</option><option value="KEY">KEY</option><option value="LOC">LOC</option><option value="SRV">SRV</option><option value="CERT">CERT</option><option value="NAPTR">NAPTR</option><option value="DS">DS</option><option value="SSHFP">SSHFP</option><option value="RRSIG">RRSIG</option><option value="NSEC">NSEC</option><option value="DNSKEY">DNSKEY</option><option value="NSEC3">DSEC3</option><option value="NSEC3PARAM">NSEC3PARAM</option><option value="TLSA">TLSA</option><option value="SPF">SPF</option><option value="DL">DL</option><option value="SOA">SOA</option></select>';
    jqTds[1].innerHTML = '<select class="form-control" id="record_type" name="record_type" value="' + aData[1]  + '"' + '>' + record_types + '</select>';
    jqTds[2].innerHTML = '<select class="form-control" id="record_status" name="record_status" value="' + aData[2]  + '"' + '><option value="false">Active</option><option value="true">Disabled</option></select>';
    jqTds[3].innerHTML = '<select class="form-control" id="record_ttl" name="record_ttl" value="' + aData[3]  + '"' + '><option value="60">1 minute</option><option value="300">5 minutes</option><option value="1800">30 minutes</option><option value="3600">60 minutes</option><option value="86400">24 hours</option></select>';
    jqTds[4].innerHTML = '<input type="text" style="display:table-cell; width:100% !important" class="form-control input-small advance-data" value="' + aData[4].replace(/\"/g,"&quot;") + '">';
    jqTds[5].innerHTML = '<button type="button" class="btn btn-flat btn-primary button_save">Save</button>';
    jqTds[6].innerHTML = '<button type="button" class="btn btn-flat btn-primary button_cancel">Cancel</button>';

    // set current value of dropdows column
    if (aData[2] == 'Active'){
        isDisabled = 'false';
    }
    else {
        isDisabled = 'true';
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