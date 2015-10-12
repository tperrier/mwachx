(function(){
  'use strict';

  angular.module('mwachx')
    .controller('UpcomingVisitsController', ['$scope','mwachxAPI',
      function ($scope, mwachxAPI) {

      mwachxAPI.pending.all('visits').getList().then(function(visits) {
        $scope.upcoming = visits.filter(function(item,index){return !item.is_bookcheck});
        $scope.bookcheks = visits.filter(function(item,index){return item.is_bookcheck});
      });


    }]);

})();
