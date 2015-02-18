window.onbeforeunload = function() {
	// Check the dirty bit
	if ($('.dirty').length > 0 ) {
		return "You have unsaved translation changes. Please click 'Done' or 'Not required' for any highlighted rows before you continue. If you choose to leave, your changes will not be saved.";
	}
}
// On DOM Load
$(function(){
	$(".btn-language").click(function(){
		mark_dirty(this);
	});
	$(".btn-translated").click(function(){
		save_translation(this);
	});
	$(".btn-not-required").click(function(){
		not_required(this);
	});

});

function has_lang(myid) {
	return $("#lang" + myid).find('input:checked').length > 0;
}

function not_required(e) {
	_ajax_that_row(e, true);
}

function save_translation(e) {
	_ajax_that_row(e, false);
}

function _ajax_that_row(e, same) {
	e = e || window.event;
    var targ = e.target || e.srcElement;
    if (targ.nodeType == 3) targ = targ.parentNode; // defeat Safari bug

    myid = $(targ).data('count');

    if( !has_lang(myid) ) {
    	$('#languageError' + myid).css('display','block');
	    $('#transError' + myid).css('display','none');
	    return;
    }
    $('#languageError' + myid).css('display','none');

    // Check for mismatch
    if($('#translated' + myid).text() != $('#original' + myid).text()) {
	    if(same){    	
    		$('#transError' + myid).css('display','block');
        	return;
        }
    } else {
		if(!same){    	
    		$('#transSameError' + myid).css('display','block');
        	return;
        }
    }

    // Made it this far, so clear the errors
	$('#transError' + myid).css('display','none');
	$('#transSameError' + myid).css('display','none');
	
	var langs = [];
	yes_langs = $("#lang" + myid).find('input:checked');
	for(var i=0;i<yes_langs.length;i++)
		langs.push($(yes_langs[i]).attr('value'));
	trans_txt = $('#translated' + myid).text();

	url = "/translation/save/"
	if(same)
		url = "/translation/notrequired/"
	$.post(url+myid,{
			translation: trans_txt,
			languages: langs,
		})
		.done(function() {
		    console.log( "success" );
		    clear_dirty(targ);
		    mw.delete_row(targ);
		})
		.fail(function() {
			console.log( "error" );
		});
}

function clear_dirty(e) {
	$(e).closest('tr').removeClass('dirty');
}

function mark_dirty (e) {
	e = e || window.event;
    var targ = e.target || e.srcElement;
    if (targ.nodeType == 3) targ = targ.parentNode; // defeat Safari bug

    $(targ).closest('tr').addClass("dirty");
}
