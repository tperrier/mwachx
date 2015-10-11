(function(){
  'use strict';

  angular.module('mwachx')
    .controller('PendingTranslationController', ['$scope','mwachxAPI','$stateParams','$location','$anchorScroll',
                '$timeout',
      function ($scope, mwachxAPI,$stateParams,$location,$anchorScroll,$timeout) {

      $scope.pending = mwachxAPI.pending.all('translations').getList().$object;
      $scope.current = $location.hash();

      // Timeout used do the DOM can render. There should be a better solution
      $timeout(function(){$anchorScroll();},500);

    }]);

})();
