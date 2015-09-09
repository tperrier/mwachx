(function(){
  'use strict';


  // Thank you: https://github.com/nnja/tweeter/blob/master/tweeter/static/tweeter/js/services.js
  // Resources have the following methods by default:
  // get(), query(), save(), remove(), delete()
  angular.module('mwachx')
    .factory('Participant', function($resource) {
      return $resource(
        '/api/v0.1/participant/:study_id/');
    })
    .factory('Message', function($resource) {
      return $resource(
        '/api/v0.1/message/:msg_id/',
        {
          study_id: '@study_id'
        });  // I *think* we need this?
    })
    .factory('mWaChxApi',['Restangular',function(Restangular){
      var service = {};

      service.participants = Restangular.withConfig(function(RestangularConfigurer) {
        RestangularConfigurer.setRestangularFields({'id':'study_id'});
      }).all('participant');
      service.facilities = Restangular.all('facilities');
      return service;
    }]);

})();
