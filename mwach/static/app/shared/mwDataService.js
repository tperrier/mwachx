(function(){
  'use strict';

angular.module('mwachx')
  .factory('mwachxAPI',['Restangular',function(Restangular){
    var service = {};

    service.participants = Restangular.all('participants');
    service.facilities = Restangular.all('facilities');

    return service;
  }])

})();
