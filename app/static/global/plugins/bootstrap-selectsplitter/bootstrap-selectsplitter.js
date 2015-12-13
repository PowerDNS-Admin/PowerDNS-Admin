+function ($) {
  'use strict';

    // CLASS DEFINITION
    // ===============================
    
    // NB: only user input triggers event change on SELECT.
    
    var SelectSplitter = function(element, options) {
        this.init('selectsplitter', element, options);
    };

    SelectSplitter.DEFAULTS = {
        template:   
                    '<div class="row" data-selectsplitter-wrapper-selector>' +

                        '<div class="col-xs-12 col-sm-6">' +
                            '<select class="form-control" data-selectsplitter-firstselect-selector></select>' +
                        '</div>' +
                        ' <!-- Add the extra clearfix for only the required viewport -->' +
                        '<div class="clearfix visible-xs-block"></div>' +
                        '<div class="col-xs-12 col-sm-6">' +
                            '<select class="form-control" data-selectsplitter-secondselect-selector></select>' +
                        '</div>' +
                        
                    '</div>'
    };
  
    /* Note: Est appelé par la fonction définie en var */
    SelectSplitter.prototype.init = function (type, element, options) {
        
        // Initial variables.
        var self = this;
        
        self.type = type;
        
        self.$element = $(element);
        self.$element.hide();
        
        self.options = $.extend( {}, SelectSplitter.DEFAULTS, options);
        
        // Get categoryParent data from $element's OPTGROUP.
        self.fullCategoryList = {};

        var optgroupCount = 0;
        var longestOptionCount = 0;

        self.$element.find('optgroup').each(function() {
            
            self.fullCategoryList[$(this).attr('label')] = {};
            
            var $that = $(this);
            
            var currentOptionCount = 0;
            $(this).find('option').each(function() {
                self.fullCategoryList[$that.attr('label')][$(this).attr('value')] = $(this).text();
                currentOptionCount++;


            });

            if (currentOptionCount > longestOptionCount) { longestOptionCount = currentOptionCount ;}
            optgroupCount++;
        });

        // Get OPTIONS for $firstSelect.
        var optionsHtml = '';
        
        for (var key in self.fullCategoryList) {
            if (self.fullCategoryList.hasOwnProperty(key)) {
                optionsHtml = optionsHtml + '<option>' + key  + '</option>';
            } 
        }
        
        // Add template.
        self.$element.after(self.options.template);
        

        // Define selected elements.
        self.$wrapper = self.$element.next('div[data-selectsplitter-wrapper-selector]'); // improved by keenthemes
        self.$firstSelect = $('select[data-selectsplitter-firstselect-selector]', self.$wrapper); // improved by keenthemes
        self.$secondSelect = $('select[data-selectsplitter-secondselect-selector]', self.$wrapper); // improved by keenthemes
        
        // Define $firstSelect and $secondSelect size attribute
        var selectSize = Math.max(optgroupCount, longestOptionCount);
        selectSize = Math.min(selectSize, 10);
        if (self.options.selectSize) {
            selectSize = self.options.selectSize; // improved by keenthemes
        }
        self.$firstSelect.attr('size', selectSize);
        self.$secondSelect.attr('size', selectSize);
        
        // Fill $firstSelect with OPTIONS
        self.$firstSelect.append(optionsHtml);
        
        // Define events.
        self.$firstSelect.on('change', $.proxy(self.updateParentCategory, self));
        self.$secondSelect.on('change', $.proxy(self.updateChildCategory, self));
        
        // Define main variables.
        self.$selectedOption = '';
        self.currentParentCategory = '';
        self.currentChildCategory = '';

        // Takes in consideration whether an option is already selected before initialization.
        // Note: .val() always returns the last value if SELECT is new. Hence cannot use .val() at init.
        // Note2: find(option:selected) retourne toujours une OPTION même lors du premier affichage.
        if ( self.$element.find('option[selected=selected]').length) {
            
            self.$selectedOption = self.$element.find('option[selected=selected]');
            
            self.currentParentCategory = self.$selectedOption.closest('optgroup').attr('label');
            self.currentChildCategory = self.$selectedOption.attr('value');
            
            self.$firstSelect.find('option:contains('+ self.currentParentCategory +')').attr('selected', 'selected');
            self.$firstSelect.trigger('change');
        }
    };

    SelectSplitter.prototype.updateParentCategory = function () {
        
        var self = this;
        
        // Update main variables.
        self.currentParentCategory = self.$firstSelect.val();
        
        self.$secondSelect.empty();

        // Définit la liste de I pour les icônes à afficher en fonction de la page.
        var optionsHtml = '';
        
        for (var key in self.fullCategoryList[self.currentParentCategory]) {
            if (self.fullCategoryList[self.currentParentCategory].hasOwnProperty(key)) {
                optionsHtml = optionsHtml + '<option value="' + key + '">' +
                                                self.fullCategoryList[self.currentParentCategory][key] +                            
                                            '</option>';
            }
        }

        self.$secondSelect.append(optionsHtml);
        
        if ( self.$selectedOption ) {
            self.$secondSelect.find( 'option[value=' + self.$selectedOption.attr('value') + ']' ).attr('selected', 'selected');
        }
    };
    
    SelectSplitter.prototype.updateChildCategory = function (event) {
                
        var self = this;

        // Update main variables.
        self.currentChildCategory = $(event.target).val(); // Note: event.target returns the SELECT, hence we must use val().

        // Remove selected items in $element SELECT, if any.
        self.$element.find('option[selected=selected]').removeAttr('selected');

        // Add selected attribute to the new selected OPTION.
        self.$element.find('option[value=' + self.currentChildCategory + ']').attr('selected', 'selected'); // Note: Adding attr also updates val().
        self.$element.trigger('change'); // Required for external plugins.

        self.$selectedOption = self.$element.find('option[selected=selected]');
    };
    
    SelectSplitter.prototype.destroy = function () {
        
        var self = this;

        self.$wrapper.remove();
  
        self.$element.removeData(self.type);
        self.$element.show();
    };

    // PLUGIN DEFINITION
    // =========================

    function Plugin(option) {
        return this.each(function() {
            var $this = $(this);
            var data = $this.data('selectsplitter');

            var options = typeof option === 'object' && option;

            if (!data && option == 'destroy') { return; }
            if (!data) { $this.data('selectsplitter', ( data = new SelectSplitter(this, options) ) ); }
            if (typeof option == 'string') { data[option](); }
        });
    }
  
    $.fn.selectsplitter = Plugin;
    /* http://stackoverflow.com/questions/10525600/what-is-the-purpose-of-fn-foo-constructor-foo-in-twitter-bootstrap-js */
    $.fn.selectsplitter.Constructor = SelectSplitter;
  

}(jQuery);
    