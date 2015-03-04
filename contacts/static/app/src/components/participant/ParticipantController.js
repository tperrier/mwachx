(function(){
  'use strict';
  
  /**
   * Main Controller for participants objects?
   * @param $scope
   * @constructor
   */
  angular.module('mwachx')
    .controller('ParticipantController', function ParticipantController($scope, Participant) {

      $scope.participants     = [];
      $scope.fullResponse     = {};
      $scope.singleModel      = 0;
      
      // Fetch all of the participants
      Participant.query(function(response) {
        // Full response has the "next" url for example.
        // maybe useful: http://stackoverflow.com/questions/24611874/django-rest-pagination-with-angularjs
        $scope.fullResponse = response;
        $scope.participants = response.results;
      });

    });

})();