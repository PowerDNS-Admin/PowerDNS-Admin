var Tasks = function () {


    return {

        //main function to initiate the module
        initDashboardWidget: function () {
			$('.task-list input[type="checkbox"]').change(function() {
				if ($(this).is(':checked')) { 
					$(this).parents('li').addClass("task-done"); 
				} else { 
					$(this).parents('li').removeClass("task-done"); 
				}
			}); 
        }

    };

}();