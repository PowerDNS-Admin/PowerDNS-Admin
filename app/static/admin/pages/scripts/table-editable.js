var TableEditable = function () {

    var handleTable = function () {

        function restoreRow(oTable, nRow) {
            var aData = oTable.fnGetData(nRow);
            var jqTds = $('>td', nRow);

            for (var i = 0, iLen = jqTds.length; i < iLen; i++) {
                oTable.fnUpdate(aData[i], nRow, i, false);
            }

            oTable.fnDraw();
        }

        function SelectElement(elementID, valueToSelect)
        {    
            var element = document.getElementById(elementID);
            element.value = valueToSelect;
        }

        function editRow(oTable, nRow) {
            var aData = oTable.fnGetData(nRow);
            var jqTds = $('>td', nRow);
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
            jqTds[4].innerHTML = '<input type="text" class="form-control input-small advance-data" value="' + aData[4] + '">';
            jqTds[5].innerHTML = '<a class="btn default btn-xs green edit" href="">Save</i></a>';
            jqTds[6].innerHTML = '<a class="btn default btn-xs green cancel" href="">Cancel</i></a>';

            // set current value of dropdows column
            if (aData[2] == 'Active'){
                isDiable = 'false';
            }
            else {
                isDiable = 'true';
            }

            SelectElement('record_type', aData[1]);
            SelectElement('record_status', isDiable);
            SelectElement('record_ttl', aData[3]);
        }

        function saveRow(oTable, nRow) {
            // var jqInputs = $('input', nRow);
            // oTable.fnUpdate(jqInputs[0].value, nRow, 0, false);
            // oTable.fnUpdate(jqInputs[1].value, nRow, 1, false);
            // oTable.fnUpdate(jqInputs[2].value, nRow, 2, false);
            // oTable.fnUpdate(jqInputs[3].value, nRow, 3, false);
            // oTable.fnUpdate(jqInputs[4].value, nRow, 4, false);

            var jqInputs = $('input', nRow);
            var jqSelect = $('select', nRow);

            if (jqSelect[1].value == 'false'){
                status = 'Active';
            }
            else {
                status = 'Disabled';
            }

            oTable.fnUpdate(jqInputs[0].value, nRow, 0, false);
            oTable.fnUpdate(jqSelect[0].value, nRow, 1, false);
            oTable.fnUpdate(status, nRow, 2, false);
            oTable.fnUpdate(jqSelect[2].value, nRow, 3, false);
            oTable.fnUpdate(jqInputs[1].value, nRow, 4, false);

            oTable.fnUpdate('<a class="btn default btn-xs purple edit" href="javascript:;"> <i class="fa fa-edit"></i></a>', nRow, 5, false);
            oTable.fnUpdate('<a class="btn default btn-xs red delete" href="javascript:;"> <i class="fa fa-trash"></i></a>', nRow, 6, false);
            oTable.fnDraw();
        }

        function cancelEditRow(oTable, nRow) {
            var jqInputs = $('input', nRow);
            oTable.fnUpdate(jqInputs[0].value, nRow, 0, false);
            oTable.fnUpdate(jqInputs[1].value, nRow, 1, false);
            oTable.fnUpdate(jqInputs[2].value, nRow, 2, false);
            oTable.fnUpdate(jqInputs[3].value, nRow, 3, false);
            oTable.fnUpdate(jqInputs[4].value, nRow, 4, false);
            oTable.fnUpdate('<a class="btn default btn-xs green edit" href="">Edit</i></a>', nRow, 5, false);
            oTable.fnDraw();
        }

        function getTableData(table) {
            var rData = []
            // get all table data
            rData = table.fnGetData();

            // reformat - pretty format
            var records = []
            rData.forEach(function(r) {
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

        function applyChanges(data, url){
             $.ajax({
                     type: "POST",
                     url: url,
                     data: JSON.stringify(data),// now data come in this function
                     contentType: "application/json; charset=utf-8",
                     crossDomain: true,
                     dataType: "json",
                     success: function (data, status, jqXHR) {
                         bootbox.alert("Applied changes record successfully.");
                     },

                     error: function (jqXHR, status) {
                         // error handler
                         console.log(jqXHR);
                         a = jqXHR;
                         bootbox.alert(jqXHR["responseText"]);
                     }
                  });
            }

        var table = $('#tbl_record_manage');

        var oTable = table.dataTable({

            // Uncomment below line("dom" parameter) to fix the dropdown overflow issue in the datatable cells. The default datatable layout
            // setup uses scrollable div(table-scrollable) with overflow:auto to enable vertical scroll(see: assets/global/plugins/datatables/plugins/bootstrap/dataTables.bootstrap.js). 
            // So when dropdowns used the scrollable div should be removed. 
            //"dom": "<'row'<'col-md-6 col-sm-12'l><'col-md-6 col-sm-12'f>r>t<'row'<'col-md-5 col-sm-12'i><'col-md-7 col-sm-12'p>>",

            "lengthMenu": [
                [5, 15, 20, -1],
                [5, 15, 20, "All"] // change per page values here
            ],

            // Or you can use remote translation file
            //"language": {
            //   url: '//cdn.datatables.net/plug-ins/3cfcc339e89/i18n/Portuguese.json'
            //},

            // set the initial value
            "pageLength": 15,

            "language": {
                "lengthMenu": " _MENU_ records"
            },
            "columnDefs": [{ // set default column settings
                'orderable': true,
                'targets': [0]
            }, {
                "searchable": true,
                "targets": [0]
            }],
            "order": [
                [0, "asc"]
            ] // set first column as a default sort by asc
        });

        var tableWrapper = $("#tbl_record_manage_new_wrapper");

        tableWrapper.find(".dataTables_length select").select2({
            showSearchInput: true //hide search box with special css class
        }); // initialize select2 dropdown

        var nEditing = null;
        var nNew = false;

        $('#tbl_record_manage_new').click(function (e) {
            e.preventDefault();

            if (nNew && nEditing) {
                bootbox.alert("Previous record not saved. Please save it before adding more record.")
                return;
            }

            var aiNew = oTable.fnAddData(['', 'A', 'Active', 3600, '', '', '']);
            var nRow = oTable.fnGetNodes(aiNew[0]);
            editRow(oTable, nRow);
            nEditing = nRow;
            nNew = true;
        });

        $('#tbl_record_manage_apply').click(function (e) {
            e.preventDefault();
            bootbox.confirm("Are you sure you want to apply the new changes?", function(result) {
                if (result == true){
                    var domain = document.getElementById('domainname').value;
                    var data = getTableData(oTable);
                    applyChanges(data, '/domain/'+ domain + '/apply');
                }
            }); 
        });

        $('#tbl_record_update_from_master').click(function (e) {
            e.preventDefault();
            var domain = document.getElementById('domainname').value;
            applyChanges({'domain': domain}, '/domain/'+ domain + '/update');
        });

        table.on('click', '.delete', function (e) {
            e.preventDefault();
            var nRow = $(this).parents('tr')[0];

            bootbox.confirm("Are you sure to delete this record?", function(result) {
                if (result == true){
                    oTable.fnDeleteRow(nRow);
                }
            }); 
        });

        table.on('click', '.cancel', function (e) {
            e.preventDefault();
            if (nNew) {
                oTable.fnDeleteRow(nEditing);
                nEditing = null;
                nNew = false;
            } else {
                restoreRow(oTable, nEditing);
                nEditing = null;
            }
        });

        table.on('click', '.edit', function (e) {
            e.preventDefault();

            /* Get the row as a parent of the link that was clicked on */
            var nRow = $(this).parents('tr')[0];

            if (nEditing !== null && nEditing != nRow) {
                /* Currently editing - but not this row - restore the old before continuing to edit mode */
                restoreRow(oTable, nEditing);
                editRow(oTable, nRow);
                nEditing = nRow;
            } else if (nEditing == nRow && this.innerHTML == "Save") {
                /* Editing this row and want to save it */
                saveRow(oTable, nEditing);
                nEditing = null;
                //alert("Updated! Do not forget to do some ajax to sync with backend :)");
            } else {
                /* No edit in progress - let's start one */
                editRow(oTable, nRow);
                nEditing = nRow;
            }
        });

        table.on('click', '.advance-data', function (e) {
            e.preventDefault();
            var nRow = $(this).parents('tr')[0];

            // get record type
            var jqSelect = $('select', nRow);
            var record_type = jqSelect[0].value;

            if (record_type == 'MX'){
                // get record data
                var jqInputs = $('input', nRow);
                var record_data = jqInputs[1].value;

                if (record_data){
                    var record_data = record_data.split(" ");
                    var mx_priority = record_data[0];
                    var mx_data = record_data[1];
                }
                else
                {
                    var mx_priority = "10";
                    var mx_data = "";
                }

                bootbox.dialog({
                    message:'Server: <input id="rdata" class="bootbox-input bootbox-input-text form-control" value="' + mx_data + '"></input><br/>Priority: <input id="rpriority" type="number" class="bootbox-input bootbox-input-text form-control" value="' + mx_priority + '"></input>',
                    title: "MX Record Data",
                    value: "makeusabrew",
                    buttons: {
                        main: {
                            label: "Save",
                            className: "btn-primary",
                            callback: function() {
                                var new_record_data = $('#rpriority').val() + " " + $('#rdata').val();
                                $('.advance-data').val(new_record_data);
                            }
                        }
                   }
                });

            }
        });

    }

    return {

        //main function to initiate the module
        init: function () {
            handleTable();
        }

    };

}();
