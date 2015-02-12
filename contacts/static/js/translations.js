window.onbeforeunload = function() {
	// Check the dirty bit
	if ($('.dirty').length > 0 ) {
		return "You have unsaved translation changes. Please click 'Done' or 'Not required' for any highlighted rows before you continue. If you choose to leave, your changes will not be saved.";
	}
}

function not_required(e) {
	e = e || window.event;
    var targ = e.target || e.srcElement;
    if (targ.nodeType == 3) targ = targ.parentNode; // defeat Safari bug

    myid = $(targ).data('count');
	yes_langs = $("#lang" + myid).find('input:checked');
	no_langs = $("#lang" + myid).find('input:not(:checked)');
	trans_txt = $('#translated' + myid).text();

	for(var i=0; i<yes_langs.length; i++) {
		console.log($(yes_langs[i]).attr('name'));
	}

	if(yes_langs.length == 0)
		$('#languageError' + myid).css('display','block');
	else 
		$('#languageError' + myid).css('display','none');

	if(trans_txt.length == 0)
		$('#transError' + myid).css('display','block');
	else 
		$('#transError' + myid).css('display','none');

}

function mark_dirty (e) {
	e = e || window.event;
    var targ = e.target || e.srcElement;
    if (targ.nodeType == 3) targ = targ.parentNode; // defeat Safari bug

    $(targ).closest('tr').addClass("dirty");
    console.log($(targ).closest('tr'));
}

$(function(){// On DOM Load

});