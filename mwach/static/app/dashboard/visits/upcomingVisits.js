(function(){
  'use strict';
  var routePrefix = '/static/app/dashboard/visits/';

  angular.module('mwachx')
    .controller('UpcomingVisitsController', ['$scope','mwachxAPI',
      function ($scope, mwachxAPI) {

      mwachxAPI.pending.all('visits').getList().then(function(visits) {
        $scope.upcoming = visits.filter(function(item,index){return item.days_overdue <= 7});
        $scope.bookchecks = visits.filter(function(item,index){return item.days_overdue > 7});
      });


    }]);

angular.module('mwachx')
  .directive('mwUpcomingVisit',[ '$modal',function($modal) {

    var pri = {
    }; // close private

    return {
      restrict:'A',templateUrl:routePrefix + 'upcomingDirective.html',
      scope: {
        'visit':'=',
        'upcoming':'=',
      },
      link: function($scope, element, attrs) {
        angular.extend($scope,{
          missedVisit:function(){
            $scope.visit.doPUT({},'seen/').then(function(result){
              // console.log('Seen',$scope.upcoming.indexOf($scope.visit ))
              $scope.upcoming.splice($scope.upcoming.indexOf($scope.visit),1);
            });
          },

          attendedVisit:function(){
            var modalInstance = $modal.open({
              templateUrl:routePrefix + 'modalVisitAttendSchedule.html',
            });

            modalInstance.result.then(function(attended){
              console.log('Save',attended);
              $scope.visit.doPUT(attended,'attended/').then(function(result){
                // console.log('Attended',result);
                $scope.upcoming.splice($scope.upcoming.indexOf($scope.visit),1);
              });
            });
          },
        }); // End Extend Scope

    } // End Link

  } // End Return Public

}]); // End Directive

})();
