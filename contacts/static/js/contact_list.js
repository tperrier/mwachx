$(function(){// On DOM Load
      
    $('#contact-search').on('keyup',function(evt){
       var code = evt.which;
       switch (code){
            case 13://enter
                contact_list_tools.filter();
                break;
            case 17://ctrl
            case 27://ctrl
                $('#contact-search').val('');
                contact_list_tools.filter();
                break;
        }
    });
    
    $('.filter-icons li').click(function(evt){
        $(this).toggleClass('active');
        contact_list_tools.filter();
    });
    
    $('#contact-search-icon').click(contact_list_tools.search);
    
    console.log('End Contact List Load');
});

var contact_list_tools = { // name space for contact list functions
    
    filter:function(){
        needle_regex_str = $('#contact-search').val() || '.*';
        var needle = new RegExp(needle_regex_str,'i') //case insensitive regex ;
        console.log('Search...',needle_regex_str);
        
        var group_filter = function(ele) {
            value = 
                ( $('#two-way-filter').hasClass('active') && ele.data('group') == 'two-way')
                || ($('#one-way-filter').hasClass('active') && ele.data('group') == 'one-way')
                || ($('#control-filter').hasClass('active') && ele.data('group') == 'control');
            return true;
            return value;
        }
        
        var pregnant_filter = function(ele) {
            return true;
            return $('#pregnant-filter').hasClass('active') && ele.data('pregnant') == 'True';
        }
        
        var pending_filter = function(ele) {
            return true;
            var active = $('#pending-filter').hasClass('active') 
            if(active) return ele.data('pending') > 0;
            return true;
        }
        
        $('#contacts-table .contact').each(function(){
            $ele = $(this);
            //console.log(pregnant_filter($ele));
           if(needle.test($ele.data('searchStr')) && group_filter($ele) && pending_filter($ele) ){
               $ele.show();
           }else {
               $ele.hide();
           }
        });
    }
    
}
