$(function(){// On DOM Load
      
    $('#contact-search').on('keyup',function(evt){
       var code = evt.which;
       switch (code){
            case 13://enter
                contact_list_tools.search();
                break;
            case 17://ctrl
                $('#contact-search').val('');
                contact_list_tools.search();
                break;
        }
    });
    
    $('#contact-search-icon').click(contact_list_tools.search);
    
    console.log('End Contact List Load');
});

var contact_list_tools = { // name space for contact list functions
    
    search:function(){
        console.log('Search...');
        needle = new RegExp($('#contact-search').val(),'i') //case insensitive regex ;
        $('#contact-list .contact').each(function(){
            $ele = $(this);
            console.log($ele);
           if(needle.test($ele.data('searchStr'))) {
               $ele.show();
           }else {
               $ele.hide();
           }
        });
    }
    
}
