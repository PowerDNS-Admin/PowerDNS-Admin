var ComponentsContextMenu = function () {

    var demo2 = function() {
        $('#main').contextmenu({
            target: '#context-menu2',
            before: function (e) {
                // This function is optional.
                // Here we use it to stop the event if the user clicks a span
                e.preventDefault();
                if (e.target.tagName == 'SPAN') {
                    e.preventDefault();
                    this.closemenu();
                    return false;
                }
                //this.getMenu().find("li").eq(2).find('a').html("Dynamically changed!");
                return true;
            }
        });
    }

    var demo3 = function() {
        // Demo 3
        $('#context2').contextmenu({
            target: '#context-menu2',
            onItem: function (context, e) {
                alert($(e.target).text());
            }
        });

        $('#context-menu2').on('show.bs.context', function (e) {
            console.log('before show event');
        });

        $('#context-menu2').on('shown.bs.context', function (e) {
            console.log('after show event');
        });

        $('#context-menu2').on('hide.bs.context', function (e) {
            console.log('before hide event');
        });

        $('#context-menu2').on('hidden.bs.context', function (e) {
            console.log('after hide event');
        });
    }

    return {
        //main function to initiate the module
        
        init: function () {
            demo2();
            demo3();
        }

    };

}();
