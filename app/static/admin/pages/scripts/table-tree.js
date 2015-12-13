var TableTree = function() {

    var demo1 = function() {

        jQuery('#gtreetable').gtreetable({
            'draggable': true,
            'source': function(id) {
                return {
                    type: 'GET',
                    url: 'demo/table_tree.php',
                    data: {
                        'id': id
                    },
                    dataType: 'json',
                    error: function(XMLHttpRequest) {
                        alert(XMLHttpRequest.status + ': ' + XMLHttpRequest.responseText);
                    }
                }
            },
            'sort': function (a, b) {          
                var aName = a.name.toLowerCase();
                var bName = b.name.toLowerCase(); 
                return ((aName < bName) ? -1 : ((aName > bName) ? 1 : 0));                            
            },
            'types': { default: 'glyphicon glyphicon-folder-open', folder: 'glyphicon glyphicon-folder-open'},
            'inputWidth': '255px'
        });
    }

    return {

        //main function to initiate the module
        init: function() {

            demo1();
        }

    };

}();