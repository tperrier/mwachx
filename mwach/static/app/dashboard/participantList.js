(function(){
  'use strict';

  /**
   * Main Controller for participants objects?
   * @param $scope
   * @constructor
   */
  angular.module('mwachx')
    .controller('ParticipantListController', ['$scope','$location','mwachxAPI',
      function ($scope, $location, mwachxAPI) {

      $scope.participants     = mwachxAPI.participants.getList().$object;
    }]);

})();
