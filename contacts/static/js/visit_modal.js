//On DOM Load
$(function(){
    $('#visitScheduleModal').on('show.bs.modal',function(evt){
        var button = $(evt.relatedTarget); //button that triggered the modal
        var visit_id = button.data('visit');
        
        var modal = $(this);
        modal.find('input[name="parent_visit_id"]').val(visit_id);
    });
});
