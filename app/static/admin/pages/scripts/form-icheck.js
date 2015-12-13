var FormiCheck = function () {


    return {
        //main function to initiate the module
        init: function () {  

            $('.icheck-colors li').click(function() {
              var self = $(this);

              if (!self.hasClass('active')) {
                  self.siblings().removeClass('active');

                var skin = self.closest('.skin'),
                  color = self.attr('class') ? '-' + self.attr('class') : '',
                  colorTmp = skin.data('color') ? '-' + skin.data('color') : '-grey',
                  colorTmp = (colorTmp === '-black' ? '' : colorTmp);

                  checkbox_default = 'icheckbox_minimal',
                  radio_default = 'iradio_minimal',
                  checkbox = 'icheckbox_minimal' + colorTmp,
                  radio = 'iradio_minimal' + colorTmp;

                if (skin.hasClass('skin-square')) {
                  checkbox_default = 'icheckbox_square';
                  radio_default = 'iradio_square';
                  checkbox = 'icheckbox_square' + colorTmp;
                  radio = 'iradio_square'  + colorTmp;
                };

                if (skin.hasClass('skin-flat')) {
                  checkbox_default = 'icheckbox_flat';
                  radio_default = 'iradio_flat';
                  checkbox = 'icheckbox_flat' + colorTmp;
                  radio = 'iradio_flat'  + colorTmp;
                };

                if (skin.hasClass('skin-line')) {
                  checkbox_default = 'icheckbox_line';
                  radio_default = 'iradio_line';
                  checkbox = 'icheckbox_line' + colorTmp;
                  radio = 'iradio_line'  + colorTmp;
                };

                skin.find('.icheck').each(function() {
                  var element = $(this).hasClass('state') ? $(this) : $(this).parent();
                  var element_class = element.attr('class').replace(checkbox, checkbox_default + color).replace(radio, radio_default + color);
                  element.attr('class', element_class);
                });

                skin.data('color', self.attr('class') ? self.attr('class') : 'black');
                self.addClass('active');
              };
            });
        }
    };
}();