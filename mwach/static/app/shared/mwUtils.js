(function() {
  'use strict';

angular.module('mwachx')
  .factory('mwachxUtils',[function(){
    var service = {};

    service.convert_form_date = function(date) {
      if ( date instanceof Date ) {
        return date.getFullYear() + '-' + (date.getMonth()+1) + '-' + date.getDate();
      } else {
        return date;
      }
    };

    return service;
  }]);

})();
