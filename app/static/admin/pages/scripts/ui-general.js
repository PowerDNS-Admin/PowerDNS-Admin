var UIGeneral = function () {

    var handlePulsate = function () {
        if (!jQuery().pulsate) {
            return;
        }

        if (Metronic.isIE8() == true) {
            return; // pulsate plugin does not support IE8 and below
        }

        if (jQuery().pulsate) {
            jQuery('#pulsate-regular').pulsate({
                color: "#bf1c56"
            });

            jQuery('#pulsate-once').click(function () {
                $('#pulsate-once-target').pulsate({
                    color: "#399bc3",
                    repeat: false
                });
            });

            jQuery('#pulsate-crazy').click(function () {
                $('#pulsate-crazy-target').pulsate({
                    color: "#fdbe41",
                    reach: 50,
                    repeat: 10,
                    speed: 100,
                    glow: true
                });
            });
        }
    }

    var handleDynamicPagination = function() {
        $('#dynamic_pager_demo1').bootpag({
            paginationClass: 'pagination',
            next: '<i class="fa fa-angle-right"></i>',
            prev: '<i class="fa fa-angle-left"></i>',
            total: 6,
            page: 1,
        }).on("page", function(event, num){
            $("#dynamic_pager_content1").html("Page " + num + " content here"); // or some ajax content loading...
        });

        $('#dynamic_pager_demo2').bootpag({
            paginationClass: 'pagination pagination-sm',
            next: '<i class="fa fa-angle-right"></i>',
            prev: '<i class="fa fa-angle-left"></i>',
            total: 24,
            page: 1,
            maxVisible: 6 
        }).on('page', function(event, num){
            $("#dynamic_pager_content2").html("Page " + num + " content here"); // or some ajax content loading...
        });
    }

    return {
        //main function to initiate the module
        init: function () {
            handlePulsate();
            handleDynamicPagination();
        }

    };

}();