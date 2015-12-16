var UserProfile = function() {
    var handleUpdatePassword = function() {
        $('.password-form').validate({
            errorElement: 'span', //default input error message container
            errorClass: 'help-block', // default input error message class
            focusInvalid: false, // do not focus the last invalid input
            ignore: "",
            rules: {
                password: {
                    required: true
                },
                rpassword: {
                    equalTo: "#newpassword"
                },
            },

            invalidHandler: function(event, validator) { //display error alert on form submit   

            },

            highlight: function(element) { // hightlight error inputs
                $(element)
                    .closest('.form-group').addClass('has-error'); // set error class to the control group
            },

            success: function(label) {
                label.closest('.form-group').removeClass('has-error');
                label.remove();
            },

            submitHandler: function(form) {
                form.submit();
            }
        });

        $('.password-form input').keypress(function(e) {
            if (e.which == 13) {
                if ($('.password-form').validate().form()) {
                    $('.password-form').submit();
                }
                return false;
            }
        });
    }

    return {
        //main function to initiate the module
        init: function() {
            handleUpdatePassword();
        }

    };

}();