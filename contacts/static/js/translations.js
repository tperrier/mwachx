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

    if($('#translated' + myid).text() != $('#original' + myid).text()) {
		$('#transError' + myid).css('display','block');
    	return;
    }
	$('#transError' + myid).css('display','none');

	// Made it through, so process the request
	yes_langs = $("#lang" + myid).find('input:checked');
	// no_langs = $("#lang" + myid).find('input:not(:checked)');
	var langs = []
	for(var i=0;i<yes_langs.length;i++) { 
		langs.push($(yes_langs[i]).attr('value'));
	}
	trans_txt = $('#translated' + myid).text();

	// Get the token.
	token = $($.find('input[name="csrfmiddlewaretoken"]')[0]).attr('value');
	// console.log(token);
	$.post("/translation/notrequired/"+myid,{
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



