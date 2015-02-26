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
    modal.find('input[type="checkbox"]').prop('checked',false);
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
    data: {'is_translated':false, 'translate_skipped':false},
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

  $('.btn-dismiss').click(function() {
    form = $(this).closest('.message').find('.msg-metadata-form');
    form.submit();
  });

  function check_msg_metadata(e,same) {
    var err_cnt = 0;
    if($(e).closest('.modal-content').find('.btn-group').find('input:checked').length == 0) {
      $(e).closest('.modal-content').find('#language-error').addClass('has-error');
      err_cnt = err_cnt + 1;
    } else 
      $(e).closest('.modal-content').find('#language-error').removeClass('has-error');

    if($(e).closest('.modal-content').find('textarea[name="message"]').val().length == 0) {
      $(e).closest('.modal-content').find('#empty-error').addClass('has-error');
      err_cnt = err_cnt + 1;
    } else 
      $(e).closest('.modal-content').find('#empty-error').removeClass('has-error');
    if( same == null )
      return err_cnt;

    if( ($(e).closest('.modal-content').find('textarea[name="message"]').val() ==
        $(e).closest('.modal-content').find('textarea[name="translation"]').val()) ==
        same
      ){
      $(e).closest('.modal-content').find('#same-error-'+String(!same)).removeClass('has-error');
      $(e).closest('.modal-content').find('#same-error-'+String(same)).addClass('has-error');
      err_cnt = err_cnt + 1;
    } else{
      $(e).closest('.modal-content').find('#same-error-'+String(same)).removeClass('has-error');
      $(e).closest('.modal-content').find('#same-error-'+String(!same)).removeClass('has-error');
    }
    return err_cnt;
  }

  function send_message(e, same, is_translated, translate_skipped) {
    same = typeof same !== 'undefined' ? same : null;
    is_translated = typeof is_translated !== 'undefined' ? is_translated : null;
    translate_skipped = typeof translate_skipped !== 'undefined' ? translate_skipped : null;
    if (check_msg_metadata(e) > 0)
      return;
    modal = $("#sendModal");
    

    // disable the buttons
    modal.find('input.btn').attr('disabled', true);

    // serialize both forms
    msg_id = modal.find('input[name="parent_id"]').val();
    var form_data = $("#send-form, form[data-message-id='" + msg_id + "']").serializeArray();
    if(is_translated) form_data.push({name: "is_translated", value: is_translated});
    if(translate_skipped) form_data.push({name: "translate_skipped", value: translate_skipped});

    $.ajax({
      url: "/contact/send/",
      type: "POST",
      data: form_data,
      success: function(data) {
        modal.find('input.btn').attr('disabled', false);
        modal.modal('toggle');
        // TODO: Refresh message list in a nicer manner!!
        location.reload();
      },
      error: function(data) {
        // TODO: Error handling.
      }
    });

  }
  // Send buttons for messages
  $('#send_t_later').click(function() {
    send_message(this);
  });
  $('#send_no_t').click(function() {
    send_message(this,false,true,true);
  });
  $('#send_t_complete').click(function() {
    send_message(this,false,true);
  });

  $('.meta-topic').change(metadata_changed);
  $('.msg-metadata-form input').change(metadata_changed);


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

function metadata_changed() {
  $this  = $(this);
  var metadata_row = $this.closest('.msg-metadata-row');
  var val = "";
  if($this.attr('type') == 'radio')
    val = $this.data('value');
  else if($this.attr('type') == 'checkbox') {
    $this.closest('.btn-group').find('input[type="checkbox"]:checked').each(function() {
      val = val + " " + this.value;
    });
  }
  else
    val = $this.val();
  // set data attribute on .msg-metadata-row
  metadata_row.data($this.attr('name'),val);
  if( metadata_row.data('relatedToggle') && 
    metadata_row.data('topic') && 
    metadata_row.data('topic') != 'none') {
    // both a topic and related have been set so activate reply/dismiss buttons
    // since they are radio buttons, no way to unset
    $this.closest('.message').find('.msg-action-btn-grp').find('.btn').removeAttr('disabled');
    $this.closest('.message').find('.msg-action-btn-grp').tooltip('disable');

  } else {
    $this.closest('.message').find('.msg-action-btn-grp').find('.btn').attr('disabled', 'disabled');
    $this.closest('.message').find('.msg-action-btn-grp').tooltip('enable');
  }

}

function refresh_participant_details(obj) {
  $(obj).find(":input").each(function() {
    if( !$(this).attr('id') )
      return;
    $("#display_" + $(this).attr('id').substr(3)).text($(this).val());
  });
}

mw.untranslated_block = "<a href='" + "{% url 'contacts.views.translations' %}" + "'><span class='badge-warning'>Untranslated</span></a>";

