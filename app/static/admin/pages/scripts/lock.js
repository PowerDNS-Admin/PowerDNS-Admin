var Lock = function () {

    return {
        //main function to initiate the module
        init: function () {

             $.backstretch([
		        "../../assets/admin/pages/media/bg/1.jpg",
    		    "../../assets/admin/pages/media/bg/2.jpg",
    		    "../../assets/admin/pages/media/bg/3.jpg",
    		    "../../assets/admin/pages/media/bg/4.jpg"
		        ], {
		          fade: 1000,
		          duration: 8000
		      });
        }

    };

}();