var ComponentsFormTools2 = function() {

    var selectSplitter = function() {
        $('#select_selectsplitter1').selectsplitter({
            selectSize: 4
        });
        $('#select_selectsplitter2').selectsplitter({
            selectSize: 6
        });
        $('#select_selectsplitter3').selectsplitter({
            selectSize: 5
        });
    }

    var miniColors = function() {
        $('.demo').each(function() {
            //
            // Dear reader, it's actually very easy to initialize MiniColors. For example:
            //
            //  $(selector).minicolors();
            //
            // The way I've done it below is just for the demo, so don't get confused
            // by it. Also, data- attributes aren't supported at this time...they're
            // only used for this demo.
            //
            $(this).minicolors({
                control: $(this).attr('data-control') || 'hue',
                defaultValue: $(this).attr('data-defaultValue') || '',
                inline: $(this).attr('data-inline') === 'true',
                letterCase: $(this).attr('data-letterCase') || 'lowercase',
                opacity: $(this).attr('data-opacity'),
                position: $(this).attr('data-position') || 'bottom left',
                change: function(hex, opacity) {
                    if (!hex) return;
                    if (opacity) hex += ', ' + opacity;
                    if (typeof console === 'object') {
                        console.log(hex);
                    }
                },
                theme: 'bootstrap'
            });

        });
    }

    return {
        //main function to initiate the module
        init: function() {
            selectSplitter();
            miniColors();
        }
    };

}();