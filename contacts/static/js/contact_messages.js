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
        var button = $(evt.relatedTarget); //button that triggered the modal
        var message_id = button.data('message-id');
        var message = button.closest('div.message');
        
        var modal = $(this);

        // Clear previous entries?
        // TODO: Should this only happen after a send?
        modal.find('textarea[name="message"]').val('');
        modal.find('textarea[name="translation"]').val('');
        if(message_id) {
            modal.find('input[name="parent_id"]').val(message_id);
            modal.find('#reply-message').show();
            modal.find('#reply-text').html(message.find('.content').html());
        }else {
            modal.find('#reply-message').hide();
        }
        
    });

    $('.transLabel').click(function() {
      // Note: This is called pre-toggle so the active check is reversed
      if(!$(this).hasClass('active'))
        $("#"+$(this).data('content-id')).text($(this).data('content-translated'));
      else
        $("#"+$(this).data('content-id')).text($(this).data('content-original'));
    });

    $('.btn-redo').click(function() {
      var message = $(this).closest('div.message');
      var tinfo = message.find('.translation-info');
      var orig_txt = message.find('.transLabel').data('content-original');
      $.ajax({
        url:  "/message/update/" + $(this).data('msg-id'),
        type: "POST",
        data: {'is_translated':false},
        success: function(data){
          // Get rid of translation toggle buttons and reset the msg
          // to the original un-translated text)
          tinfo.html(mw.untranslated_block);
          message.find('.content').html(orig_txt);
        },
        error: function() {
            // TODO: some error handling req'd
        }
      })
    });

    $('.btn-reply').click(function() {
        // TODO
        // Check that at least one language is selected
        // Check that at least related or unrelated is selected
        // Check that a topic is selected
        // AJAX send the message
        // Modify UI to remove meta-data bits and dismiss button
    });

    $('.btn-dismiss').click(function() {
        // TODO
        // Check that at least one language is selected
        // Check that at least related or unrelated is selected
        // Check that a topic is selected
        // AJAX dismiss
        // Modify UI to remove meta-data bits and dismiss button
    });

    $('.meta-language').click(function() {
        // One of the language buttons was toggled. Should save the languages
        // Dirty until save
        // mw.set_dirty(true);
        // Clear on success
        // mw.set_dirty(false);
    });

    $('.meta-related').click(function() {
        // TODO: related/unrelated were toggled in some way.
        // Dirty until save
        // mw.set_dirty(true);
        // Clear on success
        // mw.set_dirty(false);
        console.log($(this).data('value'));
    });

    $('.meta-topic').change(function() {
        // TODO: changed the topic
        // Dirty until save
        // mw.set_dirty(true);
        // Clear on success
        // mw.set_dirty(false);
        console.log($(this).val());
    });


    $('#save-details-btn').click(function() {
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
    });
});


function refresh_participant_details(obj) {
    $(obj).find(":input").each(function() {
        if( !$(this).attr('id') )
            return;
        $("#display_" + $(this).attr('id').substr(3)).text($(this).val());
    });
}

