(function(){
  'use strict';

angular.module('mwachx')
  .factory('mwachxAPI',['Restangular',function(Restangular){
    var service = {};

    service.participants = Restangular.all('participants');

    Restangular.extendModel('participants',function(participant) {
      if (participant.visits) {
        Restangular.restangularizeCollection(participant,participant.visits,'visits');
      }
      return participant;
    });

    service.facilities = Restangular.all('facilities');
    service.pending = Restangular.one('pending');

    return service;
  }])

})();
