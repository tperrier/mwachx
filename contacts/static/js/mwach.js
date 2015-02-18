/*
 * Namespace for global Javascript functions
 * Include mwach.js in website-base.html
 * Call functions like mw.delete_row(evt)
 */

window.onbeforeunload = function() {
	// Check the dirty bit
	if (mw.is_dirty()) {
		return mw.get_dirty_msg();
	}
}

var mw = function(){
    
    var pub = {}, pri = {
    	dirty_bit: false,
    	dirty_msg: "You have unsaved changes!",
    	}; // objects for public and private variables 
    

    pub.is_dirty = function() {
    	return pri.dirty_bit;
    }
    pub.set_dirty = function(b) {
    	pri.dirty_bit = b;
    }
    pub.get_dirty_msg = function() {
    	return pri.dirty_msg;
    }
    pub.set_dirty_msg = function(m) {
    	pri.dirty_bit = true;
    	pri.dirty_msg = m;
    }

    pub.delete_row = function(e){
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
    
    pub.tooltips = function(){
        $('[data-toggle="tooltip"]').tooltip()
    }
    
    /*
     * The functions below will create a header with csrftoken
     * https://gist.github.com/broinjc/db6e0ac214c355c887e5
     * We make available the mw.ajaxBeforSend() function to add to $.ajaxSetup()
     */
    pub.ajaxBeforeSend = function(xhr, settings) {
        if (!pri.csrfSafeMethod(settings.type) && pri.sameOrigin(settings.url)) {
            // Send the token to same-origin, relative URLs only.
            // Send the token only if the method warrants CSRF protection
            // Using the CSRFToken value acquired earlier
            xhr.setRequestHeader("X-CSRFToken", pri.getCookie('csrftoken'));
        }
    }
    
    pri.getCookie = function(name) {
        // This function gets cookie with a given name
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
    
    pri.csrfSafeMethod = function(method) {
	    // these HTTP methods do not require CSRF protection
	    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
	}
    
	pri.sameOrigin = function(url) {
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
    
    pri.datePad = function (n, width, z) {
       z = z || '0';
       n = n + '';
       return n.length >= width ? n : new Array(width - n.length + 1).join(z) + n;
    }
    
    pri.getDatepickerDate = function(d) {
        var day = d.getDate(), month = d.getMonth()+1;
        if (day < 10){day = '0'+day;}
        if (month < 10){month = '0'+month;}
        return day + '-' + month + '-' + d.getFullYear();
    }
    
    pri.parseDatepickerDate = function(date){
        if (typeof(date) == 'string'){
            date = date.split('-');
            if(date.length == 3){
                month = parseInt(date[1],10);
                dt = new Date(date[2],month-1,date[0])
                if (month === (dt.getMonth() + 1)){
                    return dt;
                }
            }
        }
        dt = new Date(Date.parse(date));
        if (!this.isInvalidDate(dt)) {
            return dt;
        }
        return new Date(NaN);
    }
    
    //All the makrup for datepicker, we might want to move this to a separate file and only included it when needed.
    pri.datepickerMarkup = function(){
        return 	'<div class="input-group">'+
		'<input class="form-control" id="myDatepickerInput" type="text"/>'+
		'<div class="input-group-btn">'+
			'<button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown">'+
				'<span class="mw mw-calendar"></span>'+
				'<span class="sr-only">Toggle Calendar</span>'+
			'</button>'+
			'<div class="dropdown-menu dropdown-menu-right datepicker-calendar-wrapper" role="menu">'+
				'<div class="datepicker-calendar">'+
					'<div class="datepicker-calendar-header">'+
						'<button type="button" class="prev"><span class="mw mw-chevron-left"></span><span class="sr-only">Previous Month</span></button>'+
						'<button type="button" class="next"><span class="mw mw-chevron-right"></span><span class="sr-only">Next Month</span></button>'+
						'<button type="button" class="title">'+
								'<span class="month">'+
									'<span data-month="0">January</span>'+
									'<span data-month="1">February</span>'+
									'<span data-month="2">March</span>'+
									'<span data-month="3">April</span>'+
									'<span data-month="4">May</span>'+
									'<span data-month="5">June</span>'+
									'<span data-month="6">July</span>'+
									'<span data-month="7">August</span>'+
									'<span data-month="8">September</span>'+
									'<span data-month="9">October</span>'+
									'<span data-month="10">November</span>'+
									'<span data-month="11">December</span>'+
								'</span> <span class="year"></span>'+
						'</button>'+
					'</div>'+
					'<table class="datepicker-calendar-days">'+
						'<thead>'+
						'<tr>'+
							'<th>Su</th>'+
							'<th>Mo</th>'+
							'<th>Tu</th>'+
							'<th>We</th>'+
							'<th>Th</th>'+
							'<th>Fr</th>'+
							'<th>Sa</th>'+
						'</tr>'+
						'</thead>'+
						'<tbody></tbody>'+
					'</table>'+
					'<div class="datepicker-calendar-footer">'+
						'<button type="button" class="datepicker-today">Today</button>'+
					'</div>'+
				'</div>'+
				'<div class="datepicker-wheels" aria-hidden="true">'+
					'<div class="datepicker-wheels-month">'+
						'<h2 class="header">Month</h2>'+
						'<ul>'+
							'<li data-month="0"><button type="button">Jan</button></li>'+
							'<li data-month="1"><button type="button">Feb</button></li>'+
							'<li data-month="2"><button type="button">Mar</button></li>'+
							'<li data-month="3"><button type="button">Apr</button></li>'+
							'<li data-month="4"><button type="button">May</button></li>'+
							'<li data-month="5"><button type="button">Jun</button></li>'+
							'<li data-month="6"><button type="button">Jul</button></li>'+
							'<li data-month="7"><button type="button">Aug</button></li>'+
							'<li data-month="8"><button type="button">Sep</button></li>'+
							'<li data-month="9"><button type="button">Oct</button></li>'+
							'<li data-month="10"><button type="button">Nov</button></li>'+
							'<li data-month="11"><button type="button">Dec</button></li>'+
						'</ul>'+
					'</div>'+
					'<div class="datepicker-wheels-year">'+
						'<h2 class="header">Year</h2>'+
						'<ul></ul>'+
					'</div>'+
					'<div class="datepicker-wheels-footer clearfix">'+
						'<button type="button" class="btn datepicker-wheels-back"><span class="mw mw-chevron-left"></span><span class="sr-only">Return to Calendar</span></button>'+
						'<button type="button" class="btn datepicker-wheels-select">Select <span class="sr-only">Month and Year</span></button>'+
					'</div>'+
				'</div>'+
			'</div>'+
		'</div>'+
	'</div>'
    }();
    
    
    pub.makeDatepickers = function(parent){
        $parent = parent || $('body');
        $parent.find ('.datepicker').each(function(){
            var $this = $(this);
            var id = $this.attr('id');
            //Add datepicker markup 
            $this.html(pri.datepickerMarkup);
            //Add id and name to input field
            $this.find('input').attr({id:'id_'+id,name:id});
            
            var settings = {
                formatDate: pri.getDatepickerDate,
                parseDate: pri.parseDatepickerDate,
                allowPastDates:$this.data('allow-past-dates'),
                restricted:$this.data('blackout'),
            }
            var date = $this.data('date')
            if (date) { settings['date'] = new Date(date); }
            $this.datepicker(settings);
        });
    }
    
    pub.staff_facility_select = function(evt){
        var facility_id = $(this).val();
        var url = '/staff/facility_change/'+facility_id+'/';
        $.get(url).done(function(response){window.location = response;});
    }
    
    pub.date_delta = function(evt){
        var $this = $(this);
        var direction = $this.data('direction'), delta = $this.data('delta');
        var url = '/staff/date/'+direction+'/'+delta+'/';
        console.log(url);
        $.get(url).done(function(response){window.location = response;});
    }
    
    return pub; // return public variables as namespace
}()

/*
 * Global Onload Functions
 */
 
$(function(){
    mw.tooltips();
    $.ajaxSetup({
	    beforeSend:mw.ajaxBeforeSend,
    });
    
    $('#id_staff_facility').on('change',mw.staff_facility_select);
    $('.date-delta').on('click',mw.date_delta);
    
});
