(function(){
  'use strict';

  /**
   *
   * @param $scope
   * @constructor
   */
  angular.module('mwachx')
    .controller('ParticipantNewController', ['$scope','$state','mwachxAPI','mwachxUtils',
      function ($scope, $state,mwachxAPI,mwachxUtils) {

      // Set NullBooleanField Fields
      $scope.participant = {
        hiv_disclosed:'1',
        phone_shared:'1',
        hiv_messaging:'1',
      }

      $scope.status = {
        birthdate:false,
        art_initiation:false,
        due_date:false,
      };

      $scope.submit = function(){
        console.log('Submit',$scope.participant,$scope.participantNewForm);

        // Make sure send_day and send_time are present even if they were skipped
        if ( $scope.participant.send_day === undefined) {
          $scope.participant.send_day = 0;
          $scope.participant.send_time = 8;
        }

        // Clean Dates
        $scope.participant.birthdate = mwachxUtils.convert_form_date($scope.participant.birthdate );
        $scope.participant.due_date = mwachxUtils.convert_form_date($scope.participant.due_date );
        $scope.participant.art_initiation = mwachxUtils.convert_form_date($scope.participant.art_initiation );

        $scope.participant.study_visit = mwachxUtils.convert_form_date($scope.participant.study_visit );
        $scope.participant.clinic_visit = mwachxUtils.convert_form_date($scope.participant.clinic_visit );

        if($scope.participant.study_id.length > 4) { // Study ID in form 25SSDDDD0
          $scope.participant.study_id = $scope.participant.study_id.substr(4,4); // Extract 4 digit id
        }

        mwachxAPI.participants.post($scope.participant).then(function(response){;
          console.log('Response',response);
          $state.go('participant-details',{study_id:response.study_id});
        });
      }

    }]);

})();
