//On DOM Load
$(function(){
    $('#sendModal').on('show.bs.modal',function(evt){
        var button = $(evt.relatedTarget); //button that triggered the modal
        var message_id = button.data('message');
        var message = button.closest('div.message');
        
        var modal = $(this);
        modal.find('input[name="parent_id"]').val(message_id);
        modal.find('#reply-message').html(message.find('.content').html());
        
    });
});
