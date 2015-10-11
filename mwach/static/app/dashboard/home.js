(function() {
  'use strict';

  /**
   * Main Controller for the home page
   * @param $scope
   * @constructor
   */
  angular.module('mwachx')
    .controller('HomeController',['$scope','mwachxAPI',
      function ($scope,mwachxAPI) {

        $scope.pending = mwachxAPI.pending.get().$object;

      }]);
})();
