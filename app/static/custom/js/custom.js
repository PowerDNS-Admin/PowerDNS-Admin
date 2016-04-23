function applyChanges(data, url, showResult) {
	var success = false;
	$.ajax({
		type : "POST",
		url : url,
		data : JSON.stringify(data),// now data come in this function
		contentType : "application/json; charset=utf-8",
		crossDomain : true,
		dataType : "json",
		success : function(data, status, jqXHR) {
			console.log("Applied changes successfully.")
			if (showResult) {
				var modal = $("#modal_success");
				modal.find('.modal-body p').text("Applied changes successfully");
				modal.modal('show');
			}
		},

		error : function(jqXHR, status) {
			console.log(jqXHR);
			var modal = $("#modal_error");
			modal.find('.modal-body p').text(jqXHR["responseText"]);
			modal.modal('show');
		}
	});

}