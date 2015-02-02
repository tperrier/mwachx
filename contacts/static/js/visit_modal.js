//On DOM Load
$(function(){
    $('#visitScheduleModal').on('show.bs.modal',function(evt){
        var button = $(evt.relatedTarget); //button that triggered the modal
        var study_id = button.data('study-id');
        var src = button.data('src');
        
        var modal = $(this);
        modal.find('input[name="study_id"]').val(study_id);
        modal.find('input[name="src"]').val(src);
    });
});
