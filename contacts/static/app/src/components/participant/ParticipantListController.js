(function(){
  'use strict';
  
  /**
   * Main Controller for participants objects?
   * @param $scope
   * @constructor
   */
  angular.module('mwachx')
    .controller('ParticipantListController', function ParticipantListController($scope, $location, Participant) {

      $scope.participants     = [];
      $scope.fullResponse     = {};
      
      // Methods
      $scope.loadParticipant  = loadParticipant;
      
      // Fetch all of the participants
      Participant.get(function(response) {
        // Full response has the "next" url for example.
        // maybe useful: http://stackoverflow.com/questions/24611874/django-rest-pagination-with-angularjs
        $scope.fullResponse = response;
        $scope.participants = response.results;
      });


      function loadParticipant() {
        var id = this.participant.study_id;
        $location.path('/' + id);
      }

    });

})();