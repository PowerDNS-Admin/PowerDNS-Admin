/**
 * @author Will Steinmetz
 * 
 * jQuery notification plug-in inspired by the notification style of Windows 8
 * 
 * Copyright (c)2013, Will Steinmetz
 * Licensed under the BSD license.
 * http://opensource.org/licenses/BSD-3-Clause
 */
;(function($) {
	var settings = {
		life: 10000,
		theme: 'teal',
		sticky: false,
		verticalEdge: 'right',
		horizontalEdge: 'top',
		zindex: 1100
	};
	
	var methods = {
		init: function(message, options) {
			return this.each(function() {
				var $this = $(this),
					data = $this.data('notific8');
					
                $this.data('notific8', {
                    target: $this,
                    settings: {},
                    message: ""
                });
                data = $this.data('notific8');
				data.message = message;
				
				// apply the options
				$.extend(data.settings, settings, options);
				
				// add the notification to the stack
				methods._buildNotification($this);
			});
		},
		
        /**
         * Destroy the notification
         */
		destroy: function($this) {
			var data = $this.data('notific8');
			
			$(window).unbind('.notific8');
			$this.removeData('notific8');
		},
		
		/**
		 * Build the notification and add it to the screen's stack
		 */
		_buildNotification: function($this) {
			var data = $this.data('notific8'),
				notification = $('<div />'),
				num = Number($('body').attr('data-notific8s'));
            num++;
			
			notification.addClass('jquery-notific8-notification').addClass(data.settings.theme);
			notification.attr('id', 'jquery-notific8-notification-' + num);
			$('body').attr('data-notific8s', num);
			
			// check for a heading
			if (data.settings.hasOwnProperty('heading') && (typeof data.settings.heading == "string")) {
				notification.append($('<div />').addClass('jquery-notific8-heading').html(data.settings.heading));
			}
			
			// check if the notification is supposed to be sticky
			if (data.settings.sticky) {
			    var close = $('<div />').addClass('jquery-notific8-close-sticky').append(
                    $('<span />').html('close x')
                );
                close.click(function(event) {
                    notification.animate({width: 'hide'}, {
                        duration: 'fast',
                        complete: function() {
                            notification.remove();
                        }
                    });
                });
                notification.append(close);
                notification.addClass('sticky');
            }
            // otherwise, put the normal close button up that is only display
            // when the notification is hovered over
            else {
                var close = $('<div />').addClass('jquery-notific8-close').append(
                    $('<span />').html('X')
                );
                close.click(function(event) {
                    notification.animate({width: 'hide'}, {
                        duration: 'fast',
                        complete: function() {
                            notification.remove();
                        }
                    });
                });
                notification.append(close);
            }
			
			// add the message
			notification.append($('<div />').addClass('jquery-notific8-message').html(data.message));
			
			// add the notification to the stack
			$('.jquery-notific8-container.' + data.settings.verticalEdge + '.' + data.settings.horizontalEdge).append(notification);
			
			// slide the message onto the screen
			notification.animate({width: 'show'}, {
			    duration: 'fast',
			    complete: function() {
                    if (!data.settings.sticky) {
                        (function(n, l) {
                            setTimeout(function() {
                                n.animate({width: 'hide'}, {
                                   duration: 'fast',
                                   complete: function() {
                                       n.remove();
                                   } 
                                });
                            }, l);
                        })(notification, data.settings.life);
                    }
                    data.settings = {};
                }
			});
		},
        
        /**
         * Set up the configuration settings
         */
        configure: function(options) {
            $.extend(settings, options);
        },
        
        /**
         * Set up the z-index
         */
        zindex: function(zindex) {
            settings.zindex = zindex;
        }
	};
	
	// wrapper since this plug-in is called without selecting an item first
	$.notific8 = function(message, options) {
		switch (message) {
            case 'configure':
            case 'config':
                return methods.configure.apply(this, [options]);
            break;
            case 'zindex':
                return methods.zindex.apply(this, [options]);
            break;
            default:
                if (typeof options == 'undefined') {
                    options = {};
                }
                
                // make sure that the stack containers exist
                if ($('.jquery-notific8-container').size() === 0) {
                    var $body = $('body');
                    $body.attr('data-notific8s', 0);
                    $body.append($('<div />').addClass('jquery-notific8-container').addClass('top').addClass('right'));
                    $body.append($('<div />').addClass('jquery-notific8-container').addClass('top').addClass('left'));
                    $body.append($('<div />').addClass('jquery-notific8-container').addClass('bottom').addClass('right'));
                    $body.append($('<div />').addClass('jquery-notific8-container').addClass('bottom').addClass('left'));
                    $('.jquery-notific8-container').css('z-index', settings.zindex);
                }
                
                // make sure the edge settings exist
                if ((!options.hasOwnProperty('verticalEdge')) || ((options.verticalEdge.toLowerCase() != 'right') && (options.verticalEdge.toLowerCase() != 'left'))) {
                    options.verticalEdge = settings.verticalEdge;
                }
                if ((!options.hasOwnProperty('horizontalEdge')) || ((options.horizontalEdge.toLowerCase() != 'top') && (options.horizontalEdge.toLowerCase() != 'bottom'))) {
                    options.horizontalEdge = settings.horizontalEdge;
                }
                options.verticalEdge = options.verticalEdge.toLowerCase();
                options.horizontalEdge = options.horizontalEdge.toLowerCase();
                
                //display the notification in the right corner
                $('.jquery-notific8-container.' + options.verticalEdge + '.' + options.horizontalEdge).notific8(message, options);
            break;
        }
	};
	
	// plugin setup
	$.fn.notific8 = function(message, options) {
        if (typeof message == "string") {
            return methods.init.apply(this, arguments);
        } else {
            $.error('jQuery.notific8 takes a string message as the first parameter');
        }
	};
})(jQuery);
