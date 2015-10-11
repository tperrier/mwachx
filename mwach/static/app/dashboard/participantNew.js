(function(){
  'use strict';

  /**
   *
   * @param $scope
   * @constructor
   */
  angular.module('mwachx')
    .controller('ParticipantNewController', ['$scope','$location','mwachxAPI','mwachxUtils',
      function ($scope, $location,mwachxAPI,mwachxUtils) {

      $scope.status = {
        birthdate:false,
        art_initiation:false,
        due_date:false,
      };

      $scope.participant = {}; // name space for participant

      $scope.submit = function(){
        console.log('Submit',$scope.participant,$scope.participantNewForm);

        // Clean Dates
        $scope.participant.birthdate = mwachxUtils.convert_form_date($scope.participant.birthdate );
        $scope.participant.due_date = mwachxUtils.convert_form_date($scope.participant.due_date );
        $scope.participant.art_initiation = mwachxUtils.convert_form_date($scope.participant.art_initiation );

        var response = mwachxAPI.participants.post($scope.participant);
        console.log('Response',response)
      }

    }]);

})();
