window.onbeforeunload = function() {
	// Check the dirty bit
	if ($('.dirty').length > 0 ) {
		return "You have unsaved translation changes. Please click 'Done' or 'Not required' for any highlighted rows before you continue. If you choose to leave, your changes will not be saved.";
	}
}

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
		    delete_row(targ);
		})
		.fail(function() {
			console.log( "error" );
		});
}

function delete_row(e) {
	// Thanks to: 
	// http://blog.slaks.net/2010/12/animating-table-rows-with-jquery.html
	// http://stackoverflow.com/questions/15604122/jquery-delete-table-row
	tr = $(e).closest('tr');
	tr.fadeOut(400, function(){
	    tr.remove();
	});

	tr.children('td')
        .animate({ padding: 0 })
        .wrapInner('<div />')
        .children()
        .slideUp(400, function(){});
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

$(function(){// On DOM Load
	// I'm not above copy and paste:
	// https://gist.github.com/broinjc/db6e0ac214c355c887e5

	// This function gets cookie with a given name
	function getCookie(name) {
	    var cookieValue = null;
	    if (document.cookie && document.cookie != '') {
	        var cookies = document.cookie.split(';');
	        for (var i = 0; i < cookies.length; i++) {
	            var cookie = jQuery.trim(cookies[i]);
	            // Does this cookie string begin with the name we want?
	            if (cookie.substring(0, name.length + 1) == (name + '=')) {
	                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
	                break;
	            }
	        }
	    }
	    return cookieValue;
	}
	var csrftoken = getCookie('csrftoken');
	 
	/*
	The functions below will create a header with csrftoken
	*/
	 
	function csrfSafeMethod(method) {
	    // these HTTP methods do not require CSRF protection
	    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
	}
	function sameOrigin(url) {
	    // test that a given url is a same-origin URL
	    // url could be relative or scheme relative or absolute
	    var host = document.location.host; // host + port
	    var protocol = document.location.protocol;
	    var sr_origin = '//' + host;
	    var origin = protocol + sr_origin;
	    // Allow absolute or scheme relative URLs to same origin
	    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
	        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
	        // or any other URL that isn't scheme relative or absolute i.e relative.
	        !(/^(\/\/|http:|https:).*/.test(url));
	}
	 
	$.ajaxSetup({
	    beforeSend: function(xhr, settings) {
	        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
	            // Send the token to same-origin, relative URLs only.
	            // Send the token only if the method warrants CSRF protection
	            // Using the CSRFToken value acquired earlier
	            xhr.setRequestHeader("X-CSRFToken", csrftoken);
	        }
	    }
	});
});
