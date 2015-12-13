var UIBootstrapGrowl = function() {

    return {
        //main function to initiate the module
        init: function() {


            $('#bs_growl_show').click(function(event) {

                $.bootstrapGrowl($('#growl_text').val(), {
                    ele: 'body', // which element to append to
                    type: $('#growl_type').val(), // (null, 'info', 'danger', 'success', 'warning')
                    offset: {
                        from: $('#growl_offset').val(),
                        amount: parseInt($('#growl_offset_val').val())
                    }, // 'top', or 'bottom'
                    align: $('#growl_align').val(), // ('left', 'right', or 'center')
                    width: parseInt($('#growl_width')), // (integer, or 'auto')
                    delay: $('#growl_delay').val(), // Time while the message will be displayed. It's not equivalent to the *demo* timeOut!
                    allow_dismiss: $('#glowl_dismiss').is(":checked"), // If true then will display a cross to close the popup.
                    stackup_spacing: 10 // spacing between consecutively stacked growls.
                });

            });

        }

    };

}();