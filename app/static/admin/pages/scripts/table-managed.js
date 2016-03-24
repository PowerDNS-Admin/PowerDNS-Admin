var TableManaged = function () {

    var initTableDomain = function () {

        var table = $('#tb_domain_list');

        // begin first table
        table.dataTable({

            // Internationalisation. For more info refer to http://datatables.net/manual/i18n
            "language": {
                "aria": {
                    "sortAscending": ": activate to sort column ascending",
                    "sortDescending": ": activate to sort column descending"
                },
                "emptyTable": "No data available in table",
                "info": "Showing _START_ to _END_ of _TOTAL_ domains",
                "infoEmpty": "No domains found",
                "infoFiltered": "(filtered1 from _MAX_ total domains)",
                "lengthMenu": "Show _MENU_ domains",
                "search": "Search:",
                "zeroRecords": "No matching records found"
            },

            // Or you can use remote translation file
            //"language": {
            //   url: '//cdn.datatables.net/plug-ins/3cfcc339e89/i18n/Portuguese.json'
            //},

            // Uncomment below line("dom" parameter) to fix the dropdown overflow issue in the datatable cells. The default datatable layout
            // setup uses scrollable div(table-scrollable) with overflow:auto to enable vertical scroll(see: assets/global/plugins/datatables/plugins/bootstrap/dataTables.bootstrap.js). 
            // So when dropdowns used the scrollable div should be removed. 
            //"dom": "<'row'<'col-md-6 col-sm-12'l><'col-md-6 col-sm-12'f>r>t<'row'<'col-md-5 col-sm-12'i><'col-md-7 col-sm-12'p>>",

            "bStateSave": true, // save datatable state(pagination, sort, etc) in cookie.
            
            "columns": [{
                "orderable": true
            }, {
                "orderable": true
            }, {
                "orderable": true
            }, {
                "orderable": true
            }, {
                "orderable": true
            }, {
                "orderable": false
            }],
            "lengthMenu": [
                [5, 15, 20, -1],
                [5, 15, 20, "All"] // change per page values here
            ],
            // set the initial value
            "pageLength": 10,
            "pagingType": "bootstrap_full_number",
            "language": {
                "search": "Search: ",
                "lengthMenu": "  _MENU_ records",
                "paginate": {
                    "previous":"Prev",
                    "next": "Next",
                    "last": "Last",
                    "first": "First"
                }
            },
            "columnDefs": [{  // set default column settings
                'orderable': false,
                'targets': [5]
            }, {
                "searchable": false,
                "targets": [5]
            }],
            "order": [
                [1, "asc"]
            ] // set first column as a default sort by asc
        });

        var tableWrapper = jQuery('#tb_domain_list_wrapper');

        table.find('.group-checkable').change(function () {
            var set = jQuery(this).attr("data-set");
            var checked = jQuery(this).is(":checked");
            jQuery(set).each(function () {
                if (checked) {
                    $(this).attr("checked", true);
                    $(this).parents('tr').addClass("active");
                } else {
                    $(this).attr("checked", false);
                    $(this).parents('tr').removeClass("active");
                }
            });
            jQuery.uniform.update(set);
        });

        table.on('change', 'tbody tr .checkboxes', function () {
            $(this).parents('tr').toggleClass("active");
        });

        tableWrapper.find('.dataTables_length select').addClass("form-control input-xsmall input-inline"); // modify table per page dropdown

        function getdnssec(url){
            $.getJSON(url, function(data) {
                if (data['status'] == 'error'){
                    bootbox.alert({
                        title: 'DNSSEC',
                        message: 'DNSSEC is not enabled for this domain.'
                    });
                }
                else {
                    var dnssec_msg = '';
                    var dnssec = data['dnssec'];
                    for (var i = 0; i < dnssec.length; i++) {
                        if (dnssec[i]['active']){
                            dnssec_msg += '<form class="bootbox-form">'+
                            '<h3><strong>'+dnssec[i]['keytype']+'</strong></h3>'+
                            '<strong>DNSKEY</strong>'+
                            '<input class="bootbox-input bootbox-input-text form-control" autocomplete="off" type="text" readonly="true" value="'+dnssec[i]['dnskey']+'">'+
                            '</form>'+
                            '<br/>';
                            if(dnssec[i]['ds']){
                                var dsList = dnssec[i]['ds'];
                                dnssec_msg += '<strong>DS</strong>';
                                for (var j = 0; j < dsList.length; j++){
                                    dnssec_msg += '<input class="bootbox-input bootbox-input-text form-control" autocomplete="off" type="text" readonly="true" value="'+dsList[j]+'">';
                                }
                            }
                        }
                    }
                    bootbox.alert({
                        title: 'DNSSEC',
                        message: dnssec_msg
                    });
                }
            });
        }

        table.on('click', '.dnssec', function (e) {
            e.preventDefault();
            var nRow = $(this).parents('tr')[0];
            var domain_name = nRow.cells[0].innerText;
            getdnssec('/domain/'+ domain_name +'/dnssec');
        });

    }

    var initTableConfig = function () {

        var table = $('#tb_config_list');

        // begin first table
        table.dataTable({

            // Internationalisation. For more info refer to http://datatables.net/manual/i18n
            "language": {
                "aria": {
                    "sortAscending": ": activate to sort column ascending",
                    "sortDescending": ": activate to sort column descending"
                },
                "emptyTable": "No data available in table",
                "info": "Showing _START_ to _END_ of _TOTAL_ configs",
                "infoEmpty": "No configs found",
                "infoFiltered": "(filtered1 from _MAX_ total configs)",
                "lengthMenu": "Show _MENU_ configs",
                "search": "Search:",
                "zeroRecords": "No matching configs found"
            },

            // Or you can use remote translation file
            //"language": {
            //   url: '//cdn.datatables.net/plug-ins/3cfcc339e89/i18n/Portuguese.json'
            //},

            // Uncomment below line("dom" parameter) to fix the dropdown overflow issue in the datatable cells. The default datatable layout
            // setup uses scrollable div(table-scrollable) with overflow:auto to enable vertical scroll(see: assets/global/plugins/datatables/plugins/bootstrap/dataTables.bootstrap.js). 
            // So when dropdowns used the scrollable div should be removed. 
            //"dom": "<'row'<'col-md-6 col-sm-12'l><'col-md-6 col-sm-12'f>r>t<'row'<'col-md-5 col-sm-12'i><'col-md-7 col-sm-12'p>>",

            "bStateSave": true, // save datatable state(pagination, sort, etc) in cookie.
            
            "columns": [{
                "orderable": false
            }, {
                "orderable": true
            }, {
                "orderable": true
            }],
            "lengthMenu": [
                [5, 15, 20, -1],
                [5, 15, 20, "All"] // change per page values here
            ],
            // set the initial value
            "pageLength": 20,            
            "pagingType": "bootstrap_full_number",
            "language": {
                "search": "Search: ",
                "lengthMenu": "  _MENU_ configs",
                "paginate": {
                    "previous":"Prev",
                    "next": "Next",
                    "last": "Last",
                    "first": "First"
                }
            },
            "columnDefs": [{  // set default column settings
                'orderable': false,
                'targets': [0]
            }, {
                "searchable": false,
                "targets": [0]
            }],
            "order": [
                [2, "asc"]
            ] // set first column as a default sort by asc
        });

        var tableWrapper = jQuery('#tb_config_list_wrapper');

        table.find('.group-checkable').change(function () {
            var set = jQuery(this).attr("data-set");
            var checked = jQuery(this).is(":checked");
            jQuery(set).each(function () {
                if (checked) {
                    $(this).attr("checked", true);
                    $(this).parents('tr').addClass("active");
                } else {
                    $(this).attr("checked", false);
                    $(this).parents('tr').removeClass("active");
                }
            });
            jQuery.uniform.update(set);
        });

        table.on('change', 'tbody tr .checkboxes', function () {
            $(this).parents('tr').toggleClass("active");
        });

        tableWrapper.find('.dataTables_length select').addClass("form-control input-xsmall input-inline"); // modify table per page dropdown
    }

    var initTableStastic = function () {

        var table = $('#tb_stastic_list');

        // begin first table
        table.dataTable({

            // Internationalisation. For more info refer to http://datatables.net/manual/i18n
            "language": {
                "aria": {
                    "sortAscending": ": activate to sort column ascending",
                    "sortDescending": ": activate to sort column descending"
                },
                "emptyTable": "No data available in table",
                "info": "Showing _START_ to _END_ of _TOTAL_ stastics",
                "infoEmpty": "No stastics found",
                "infoFiltered": "(filtered1 from _MAX_ total stastics)",
                "lengthMenu": "Show _MENU_ stastics",
                "search": "Search:",
                "zeroRecords": "No matching stastics found"
            },

            // Or you can use remote translation file
            //"language": {
            //   url: '//cdn.datatables.net/plug-ins/3cfcc339e89/i18n/Portuguese.json'
            //},

            // Uncomment below line("dom" parameter) to fix the dropdown overflow issue in the datatable cells. The default datatable layout
            // setup uses scrollable div(table-scrollable) with overflow:auto to enable vertical scroll(see: assets/global/plugins/datatables/plugins/bootstrap/dataTables.bootstrap.js). 
            // So when dropdowns used the scrollable div should be removed. 
            //"dom": "<'row'<'col-md-6 col-sm-12'l><'col-md-6 col-sm-12'f>r>t<'row'<'col-md-5 col-sm-12'i><'col-md-7 col-sm-12'p>>",

            "bStateSave": true, // save datatable state(pagination, sort, etc) in cookie.
            
            "columns": [{
                "orderable": false
            }, {
                "orderable": true
            }, {
                "orderable": true
            }],
            "lengthMenu": [
                [5, 15, 20, -1],
                [5, 15, 20, "All"] // change per page values here
            ],
            // set the initial value
            "pageLength": 20,            
            "pagingType": "bootstrap_full_number",
            "language": {
                "search": "Search: ",
                "lengthMenu": "  _MENU_ stastics",
                "paginate": {
                    "previous":"Prev",
                    "next": "Next",
                    "last": "Last",
                    "first": "First"
                }
            },
            "columnDefs": [{  // set default column settings
                'orderable': false,
                'targets': [0]
            }, {
                "searchable": false,
                "targets": [0]
            }],
            "order": [
                [2, "asc"]
            ] // set first column as a default sort by asc
        });

        var tableWrapper = jQuery('#tb_stastic_list_wrapper');

        table.find('.group-checkable').change(function () {
            var set = jQuery(this).attr("data-set");
            var checked = jQuery(this).is(":checked");
            jQuery(set).each(function () {
                if (checked) {
                    $(this).attr("checked", true);
                    $(this).parents('tr').addClass("active");
                } else {
                    $(this).attr("checked", false);
                    $(this).parents('tr').removeClass("active");
                }
            });
            jQuery.uniform.update(set);
        });

        table.on('change', 'tbody tr .checkboxes', function () {
            $(this).parents('tr').toggleClass("active");
        });

        tableWrapper.find('.dataTables_length select').addClass("form-control input-xsmall input-inline"); // modify table per page dropdown
    }

    var initTableUser = function () {

        function applyChanges(data, url, showResult){
            $.ajax({
                 type: "POST",
                 url: url,
                 data: JSON.stringify(data),// now data come in this function
                 contentType: "application/json; charset=utf-8",
                 crossDomain: true,
                 dataType: "json",
                 success: function (data, status, jqXHR) {
                    if (showResult){
                        bootbox.alert("Applied changes successfully.");
                    }
                    else{
                        console.log("Applied changes successfully.")
                    }
                 },

                 error: function (jqXHR, status) {
                     // error handler
                     console.log(jqXHR);
                     a = jqXHR;
                     bootbox.alert(jqXHR["responseText"]);
                 }
              });
        }

        var table = $('#tbl_user_manage');

        // begin first table
        table.dataTable({

            // Internationalisation. For more info refer to http://datatables.net/manual/i18n
            "language": {
                "aria": {
                    "sortAscending": ": activate to sort column ascending",
                    "sortDescending": ": activate to sort column descending"
                },
                "emptyTable": "No data available in table",
                "info": "Showing _START_ to _END_ of _TOTAL_ users",
                "infoEmpty": "No users found",
                "infoFiltered": "(filtered1 from _MAX_ total users)",
                "lengthMenu": "Show _MENU_ users",
                "search": "Search:",
                "zeroRecords": "No matching users found"
            },

            // Or you can use remote translation file
            //"language": {
            //   url: '//cdn.datatables.net/plug-ins/3cfcc339e89/i18n/Portuguese.json'
            //},

            // Uncomment below line("dom" parameter) to fix the dropdown overflow issue in the datatable cells. The default datatable layout
            // setup uses scrollable div(table-scrollable) with overflow:auto to enable vertical scroll(see: assets/global/plugins/datatables/plugins/bootstrap/dataTables.bootstrap.js). 
            // So when dropdowns used the scrollable div should be removed. 
            //"dom": "<'row'<'col-md-6 col-sm-12'l><'col-md-6 col-sm-12'f>r>t<'row'<'col-md-5 col-sm-12'i><'col-md-7 col-sm-12'p>>",

            "bStateSave": true, // save datatable state(pagination, sort, etc) in cookie.
            
            "columns": [{
                "orderable": true
            }, {
                "orderable": true
            }, {
                "orderable": true
            }, {
                "orderable": false
            }, {
                "orderable": false
            }, {
                "orderable": false
            }],
            "lengthMenu": [
                [5, 15, 20, -1],
                [5, 15, 20, "All"] // change per page values here
            ],
            // set the initial value
            "pageLength": 5,            
            "pagingType": "bootstrap_full_number",
            "language": {
                "search": "Search: ",
                "lengthMenu": "  _MENU_ users",
                "paginate": {
                    "previous":"Prev",
                    "next": "Next",
                    "last": "Last",
                    "first": "First"
                }
            },
            "columnDefs": [{  // set default column settings
                'orderable': false,
                'targets': [0]
            }, {
                "searchable": true,
                "targets": [0]
            }],
            "order": [
                [1, "asc"]
            ] // set first column as a default sort by asc
        });

        var tableWrapper = jQuery('#tb_user_manage_wrapper');

        table.find('.group-checkable').change(function () {
            var set = jQuery(this).attr("data-set");
            var checked = jQuery(this).is(":checked");
            jQuery(set).each(function () {
                if (checked) {
                    $(this).attr("checked", true);
                    $(this).parents('tr').addClass("active");
                } else {
                    $(this).attr("checked", false);
                    $(this).parents('tr').removeClass("active");
                }
            });
            jQuery.uniform.update(set);
        });

        table.on('change', 'tbody tr .checkboxes', function () {
            $(this).parents('tr').toggleClass("active");
        });

        tableWrapper.find('.dataTables_length select').addClass("form-control input-xsmall input-inline"); // modify table per page dropdown


        // Buton action handling
        table.on('click', '.revoke', function (e) {
            e.preventDefault();

            var nRow = $(this).parents('tr')[0];
            var username = nRow.cells.item(0).innerText;

            bootbox.confirm("Are you sure to revoke all " + username+ "'s privileges?. He will not able to access to any domain.", function(result) {
                if (result == true){
                    var postdata = {'action': 'revoke_user_privielges', 'data': username}
                    applyChanges(postdata, '/admin/manageuser');
                }
            }); 
        });

        table.on('click', '.delete', function (e) {
            e.preventDefault();

            var nRow = $(this).parents('tr')[0];
            var username = nRow.cells.item(0).innerText;

            bootbox.confirm("Are you sure to delete user " + username + "?", function(result) {
                if (result == true){
                    var postdata = {'action': 'delete_user', 'data': username}
                    applyChanges(postdata, '/admin/manageuser');
                }
            }); 
        });

        table.on('change', '.ck_admin', function (e) {
            e.preventDefault();

            var nRow = $(this).parents('tr')[0];
            var username = nRow.cells.item(0).innerText;
            var ckadmin = document.getElementById("ck_admin_" + username).checked;
            
            if (ckadmin){
                postdata = {'action': 'set_admin', 'data': {'username': username, 'is_admin': true}};
                applyChanges(postdata, '/admin/manageuser');
            }
            else{
                postdata = {'action': 'set_admin', 'data': {'username': username, 'is_admin': false}};
                applyChanges(postdata, '/admin/manageuser');
            }
        });

    }

    var initTableHistory = function () {

        function applyChanges(data, url, showResult){
            $.ajax({
                 type: "POST",
                 url: url,
                 data: JSON.stringify(data),// now data come in this function
                 contentType: "application/json; charset=utf-8",
                 crossDomain: true,
                 dataType: "json",
                 success: function (data, status, jqXHR) {
                    if (showResult){
                        bootbox.alert("Applied changes successfully.");
                    }
                    else{
                        console.log("Applied changes successfully.")
                    }
                 },

                 error: function (jqXHR, status) {
                     // error handler
                     console.log(jqXHR);
                     a = jqXHR;
                     bootbox.alert(jqXHR["responseText"]);
                 }
              });
        }

        var table = $('#tbl_history');

        // begin first table
        table.dataTable({

            // Internationalisation. For more info refer to http://datatables.net/manual/i18n
            "language": {
                "aria": {
                    "sortAscending": ": activate to sort column ascending",
                    "sortDescending": ": activate to sort column descending"
                },
                "emptyTable": "No data available in table",
                "info": "Showing _START_ to _END_ of _TOTAL_ histories",
                "infoEmpty": "No histories found",
                "infoFiltered": "(filtered1 from _MAX_ total histories)",
                "lengthMenu": "Show _MENU_ histories",
                "search": "Search:",
                "zeroRecords": "No matching histories found"
            },

            // Or you can use remote translation file
            //"language": {
            //   url: '//cdn.datatables.net/plug-ins/3cfcc339e89/i18n/Portuguese.json'
            //},

            // Uncomment below line("dom" parameter) to fix the dropdown overflow issue in the datatable cells. The default datatable layout
            // setup uses scrollable div(table-scrollable) with overflow:auto to enable vertical scroll(see: assets/global/plugins/datatables/plugins/bootstrap/dataTables.bootstrap.js). 
            // So when dropdowns used the scrollable div should be removed. 
            //"dom": "<'row'<'col-md-6 col-sm-12'l><'col-md-6 col-sm-12'f>r>t<'row'<'col-md-5 col-sm-12'i><'col-md-7 col-sm-12'p>>",

            "bStateSave": true, // save datatable state(pagination, sort, etc) in cookie.
            
            "columns": [{
                "orderable": true
            }, {
                "orderable": true
            }, {
                "orderable": true
            }, {
                "orderable": false
            }],
            "lengthMenu": [
                [5, 15, 20, -1],
                [5, 15, 20, "All"] // change per page values here
            ],
            // set the initial value
            "pageLength": 20,            
            "pagingType": "bootstrap_full_number",
            "language": {
                "search": "Search: ",
                "lengthMenu": "  _MENU_ histories",
                "paginate": {
                    "previous":"Prev",
                    "next": "Next",
                    "last": "Last",
                    "first": "First"
                }
            },
            "columnDefs": [{  // set default column settings
                'orderable': false,
                'targets': [0]
            }, {
                "searchable": true,
                "targets": [0]
            }],
            "order": [
                [2  , "desc"]
            ] // set first time column as a default sort by desc
        });

        var tableWrapper = jQuery('#tbl_history_wrapper');

        table.find('.group-checkable').change(function () {
            var set = jQuery(this).attr("data-set");
            var checked = jQuery(this).is(":checked");
            jQuery(set).each(function () {
                if (checked) {
                    $(this).attr("checked", true);
                    $(this).parents('tr').addClass("active");
                } else {
                    $(this).attr("checked", false);
                    $(this).parents('tr').removeClass("active");
                }
            });
            jQuery.uniform.update(set);
        });

        table.on('change', 'tbody tr .checkboxes', function () {
            $(this).parents('tr').toggleClass("active");
        });

        tableWrapper.find('.dataTables_length select').addClass("form-control input-xsmall input-inline"); // modify table per page dropdown

        table.on('click', '.history_detail', function (e) {
            e.preventDefault();
            var nRow = $(this).parents('tr')[0];
            var detail = nRow.cells.item(3).children[0].value;
            bootbox.alert(detail);
        });

        $('#tbl_history_clear').click(function (e) {
            e.preventDefault();
            bootbox.confirm("Are you sure you want to remove all history?", function(result) {
                if (result == true){
                    applyChanges('', '/admin/history');
                    location.reload();
                }
            }); 
        });

    }


    return {

        //main function to initiate the module
        init: function () {
            if (!jQuery().dataTable) {
                return;
            }

            initTableDomain();
            initTableConfig();
            initTableStastic();
            initTableUser();
            initTableHistory();
        }

    };

}();