(function(){
  'use strict';

  angular.module('mwachx')
    .controller('PendingMessageController', ['$scope','mwachxAPI',
      function ($scope, mwachxAPI) {

      $scope.pending = mwachxAPI.pending.all('messages').getList().$object;

    }]);

})();
