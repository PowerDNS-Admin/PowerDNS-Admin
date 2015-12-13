var MyButtonAction = function () {

    var handleButton = function () {

        function postJson(data, url){
             $.ajax({
                     type: "POST",
                     url: url,
                     data: JSON.stringify(data),// now data come in this function
                     contentType: "application/json; charset=utf-8",
                     crossDomain: true,
                     dataType: "json",
                     success: function (data, status, jqXHR) {
                         bootbox.alert("Applied changes record successfully.");
                     },

                     error: function (jqXHR, status) {
                         // error handler
                         console.log(jqXHR);
                         a = jqXHR;
                         bootbox.alert(jqXHR["responseText"]);
                     }
                  });
            }


        $('#delete_domain').click(function (e) {
            e.preventDefault();
            bootbox.confirm("Are you sure you want to delete this domain?", function(result) {
                if (result == true){
                    var domain = document.getElementById('delete_domain').value;
                    $.get("/admin/domain/"+ domain +"/delete");
                    window.location.href = '/';
                }
            }); 
        });
    }

    return {
        //main function to initiate the module
        init: function () {
            handleButton();
        }
    };
}();