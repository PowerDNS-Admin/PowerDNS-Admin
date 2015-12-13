var ComponentsDropdowns = function () {

    var handleMultiSelect = function () {
        $('#domain_multi_user').multiSelect();
    }

    return {
        //main function to initiate the module
        init: function () {
            handleMultiSelect();
        }
    };

}();