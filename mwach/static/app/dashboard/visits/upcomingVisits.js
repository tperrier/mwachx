(function(){
  'use strict';

  angular.module('mwachx')
    .controller('UpcomingVisitsController', ['$scope','mwachxAPI',
      function ($scope, mwachxAPI) {

      mwachxAPI.pending.all('visits').getList().then(function(visits) {
        $scope.upcoming = visits.filter(function(item,index){return item.days_overdue <= 7});
        $scope.bookchecks = visits.filter(function(item,index){return item.days_overdue > 7});
      });


    }]);

})();
