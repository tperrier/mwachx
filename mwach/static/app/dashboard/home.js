(function() {
  'use strict';

  /**
   * Main Controller for the home page
   * @param $scope
   * @constructor
   */
  angular.module('mwachx')
    .controller('HomeController',['$scope','mwachxAPI','mwachxDjango',
      function ($scope,mwachxAPI,mwachxDjango) {

        $scope.pending = mwachxAPI.pending.get().$object;
        $scope.isAdmin = mwachxDjango.isAdmin;

      }]);
})();
