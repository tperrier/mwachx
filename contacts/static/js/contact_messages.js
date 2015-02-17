// On DOM Load
$(function(){
    $('#sendModal').find('textarea[name="message"]').on('keydown', function() {
        var msg = $(this).val();
        var translation = $('textarea[name="translation"]').val() || "";
        if( msg.localeCompare(translation) == 0)
            $(this).data('copy',true);
        else 
            $(this).data('copy',false);
    });
    $('#sendModal').find('textarea[name="message"]').bind('input propertychange', function() {
        if( $(this).data('copy') )
            $('textarea[name="translation"]').val($(this).val());
    });
    $('#sendModal').on('show.bs.modal',function(evt){
        // TODO: do we need to clear the previous input here?

        var button = $(evt.relatedTarget); //button that triggered the modal
        var message_id = button.data('message-id');
        var message = button.closest('div.message');
        
        var modal = $(this);
        console.log('Message: ',message_id);
        if(message_id) {
            modal.find('input[name="parent_id"]').val(message_id);
            modal.find('#reply-message').show();
            modal.find('#reply-text').html(message.find('.content').html());
            modal.find('#metadata').html(message.find('.msg-metadata-row').html());

            // FIX: Carry over the select
            var val = message.find(':selected').val();
            modal.find('option[value="' + val + '"]').attr('selected', true);

            // Have to refresh tooltips now that they are here too.
            mw.tooltips();
        }else {
            modal.find('#reply-message').hide();
        }
        
    });
});


function refresh_participant_details(obj) {
    $(obj).find(":input").each(function() {
        if( !$(this).attr('id') )
            return;
        $("#display_" + $(this).attr('id').substr(3)).text($(this).val());
    });
}

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
            }
            else {
                // Close the modal
                $(modal).find('button').attr('disabled', false);
                $(modal).modal('toggle');
                refresh_participant_details($(form_id));
            }   
        },
        error: function () {
            // TODO: Need to do some AJAXiness here
            $(form_id).find('.error-message').show()
            $(modal).find('button').attr('disabled', false);    
        }
    });
}