function save_visit(e) {
	// Ensure we selected type
	if( !$('input:radio[name=visit_type]:checked').val()) {
		$("#visit_type_block").addClass('has-error');
		return;
	}

	e = e || window.event;
	var targ = e.target || e.srcElement;
	if (targ.nodeType == 3) targ = targ.parentNode; // defeat Safari bug
	url = $(targ).data('post-url');

	$('#visitScheduleModal').find('button').attr('disabled', true);

	$.post(url,{
		arrived: $("input[name=arrived]").val(),
		next_visit: $("input[name=next_visit]").val(),
		visit_type: $('input:radio[name=visit_type]:checked').val(),
		study_id: $("input[name=study_id]").val(),
	})
	.done(function() {
		console.log('success');
		$('#visitScheduleModal').find('button').attr('disabled', false);
		$('#visitScheduleModal').modal('toggle');
		id = $('#visitScheduleModal').find("#save_button").data('row-id');
		delete_row($("#" + id));
	})
	.fail(function() {
		console.log('error');
		// TODO: Add some error handling here. What is the right approach?
		// Should we tell the user? Try again? Right now the modal will just stay open.
	});
}

$(function(){ // On DOM Load
    $('#visitScheduleModal').on('show.bs.modal',function(evt){
        var button = $(evt.relatedTarget); //button that triggered the modal
        var study_id = button.data('study-id');
        var src = button.data('src');
        var row_id = button.attr('id');
        
        var modal = $(this);
        modal.find('input[name="study_id"]').val(study_id);
        modal.find('input[name="src"]').val(src);
        console.log(row_id);
	    modal.find("#save_button").data('row-id', row_id);
    });

    $(".dismiss-btn").click(function(e) {
    	me = $(this);
    	url = me.data('post-url');
    	$.post(url, {})
			.done(function() {
				delete_row(me);
			})
			.fail(function() {
				// TODO: add some error handling here.
			});
    });
});
