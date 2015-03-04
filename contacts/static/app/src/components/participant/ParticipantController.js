(function(){
  'use strict';
  
  /**
   * Main Controller for participants objects?
   * @param $scope
   * @constructor
   */
  angular.module('mwachx')
    .controller('ParticipantController', 
      function ParticipantController($scope, $location, $routeParams, 
        Message, Participant) {

        $scope.participant      = [];
        $scope.fullResponse     = {};

        $scope.messages         = [];
        
        // Methods
        
        // Fetch this participant
        Participant.get( {study_id:$routeParams.study_id},
          function(response) {
            $scope.participant = response;
        });

        // Fetch messages for this participant
        Message.query( {study_id:$routeParams.study_id},
          function(response) {
            
            $scope.messages = response;
            for (var i = $scope.messages.length - 1; i >= 0; i--) {
              if ($scope.messages[i].is_system == false && $scope.messages[i].is_outgoing == true) {
                $scope.messages[i].is_nurse = true;
              } else {
                $scope.messages[i].is_nurse = false;
              }

            };
        });

      });

})();