// On DOM Load
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



function save_participant_details(e) {
    form_id = "#participant-details-form";
    modal = "#contactDetailsModal";

    $(modal).find('button').attr('disabled', true);

    $.ajax({
        url: "/participant/update/" + $(modal).data('participant-id') + "/",
        type: "POST",
        data: $(form_id).serialize(),
        success: function(data) {
            if (!(data['success'])) {
                // Here we replace the form if there's an error
                $(form_id).replaceWith(data['form_html']);
                $(modal).find('button').attr('disabled', false);
                console.log('there was an error returned');
                console.log(data);
            }
            else {
                // Close the modal
                $(modal).find('button').attr('disabled', false);
                $(modal).modal('toggle');
                console.log('ok, great!');

            }   
        },
        error: function () {
            // TODO: Need to do some AJAXiness here
            $(form_id).find('.error-message').show()
            $(modal).find('button').attr('disabled', false);    
        }
    });
}