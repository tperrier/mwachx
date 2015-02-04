//On DOM Load
$(function(){
    $('#sendModal').on('show.bs.modal',function(evt){
        var button = $(evt.relatedTarget); //button that triggered the modal
        var message_id = button.data('message-id');
        var message = button.closest('div.message');
        
        var modal = $(this);
        console.log('Message: ',message_id);
        if(message_id) {
            modal.find('input[name="parent_id"]').val(message_id);
            modal.find('#reply-message').show().html(message.find('.content').html());
        }else {
            modal.find('#reply-message').hide();
        }
        
    });
});
