(function(){
  'use strict';

  angular.module('mwachx')
    .controller('PendingTranslationController', ['$scope','mwachxAPI',
      function ($scope, mwachxAPI) {

      $scope.pending = mwachxAPI.pending.all('translations').getList().$object;

    }]);

})();
