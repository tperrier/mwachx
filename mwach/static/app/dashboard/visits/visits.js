(function(){
  'use strict';
  var routePrefix = '/static/app/dashboard/visits/';

angular.module('mwachx') .controller('PendingVisitsController',
  ['$scope','mwachxAPI',
  function ($scope, mwachxAPI) {

    mwachxAPI.pending.all('visits').getList().then(function(visits) {
      $scope.current = visits.filter(function(item,index){return item.days_overdue <= 7});
      $scope.bookchecks = visits.filter(function(item,index){return item.days_overdue > 7});
    });

}]);

angular.module('mwachx') .controller('UpcomingVisitsController',
  ['$scope','mwachxAPI',
  function ($scope, mwachxAPI) {

    $scope.upcoming = mwachxAPI.visits.all('upcoming').getList().$object;

}]);

angular.module('mwachx')
  .directive('mwPendingVisit',[ '$modal',function($modal) {

    return {
      restrict:'A',templateUrl:routePrefix + 'pendingVisitDirective.html',
      scope: {
        'visit':'=',
        'visits':'=',
      },
      link: function($scope, element, attrs) {
        angular.extend($scope,{
          missedVisit:function($event){
            $event.stopPropagation();
            $scope.visit.doPUT({},'seen/').then(function(result){
              // console.log('Seen',$scope.upcoming.indexOf($scope.visit ))
              $scope.visits.splice($scope.visits.indexOf($scope.visit),1);
            });
          },

          attendedVisit:function($event){
            $event.stopPropagation();
            var modalInstance = $modal.open({
              templateUrl:routePrefix + 'modalVisitAttendSchedule.html',
            });

            modalInstance.result.then(function(attended){
              console.log('Save',attended);
              $scope.visit.doPUT(attended,'attended/').then(function(result){
                // console.log('Attended',result);
                $scope.visits.splice($scope.visits.indexOf($scope.visit),1);
              });
            });
          },
        }); // End Extend Scope

    } // End Link

  } // End Return Public

}]); // End Directive

})();
