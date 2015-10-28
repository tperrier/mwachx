(function(){
  'use strict';

  /**
   * Main Controller for participants objects?
   * @param $scope
   * @constructor
   */
  angular.module('mwachx').controller('ParticipantListController',
  ['$scope','$stateParams','mwachxAPI',
  function ($scope, $stateParams, mwachxAPI) {

      $scope.participants = mwachxAPI.participants.getList().$object;
      $scope.alerts = [$stateParams.message];
      $scope.closeAlert = function(i){$scope.alerts.splice(i,1)}
    }]);

})();
