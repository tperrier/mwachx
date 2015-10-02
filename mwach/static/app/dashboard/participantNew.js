(function(){
  'use strict';

  /**
   *
   * @param $scope
   * @constructor
   */
  angular.module('mwachx')
    .controller('ParticipantNewController', ['$scope','$location','mwachxAPI',
      function ($scope, $location,mwachxAPI) {

      $scope.status = {
        birthdate:false,
        art_initiation:false,
        due_date:false,
      };

      $scope.submit = function(){
        console.log('Submit',$scope.participant,$scope.participantNewForm);
        mwachxAPI.participants.post($scope.participant)
      }

    }]);

})();
