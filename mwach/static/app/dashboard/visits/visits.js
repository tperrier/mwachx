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
  .directive('mwPendingVisit',[ '$modal','mwachxUtils',
  function($modal,mwachxUtils) {

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

            var $modalScope = $scope.$new(true);
            $modalScope.study_base_date = new Date($scope.visit.participant.study_base_date);
            var modalInstance = $modal.open({
              templateUrl:routePrefix + 'modalVisitAttendSchedule.html',
              scope:$modalScope,
              controller: 'VisitModifyModalController',
            });

            modalInstance.result.then(function(attended){
              mwachxUtils.convert_dates(attended);
              console.log('Attended',attended);
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

// *************************************
// Modal Controllers
// *************************************

angular.module('mwachx') .controller('VisitModifyModalController',
  ['$scope','$modalInstance',
  function ($scope, $modalInstance) {
    $scope.today = new Date();
    $scope.attended = {
      'study_visit_type':undefined,
      'type':undefined,
    }

    $scope.$watch('attended.study_visit_type',function(newValue,oldValue) {
      // automatically set study visit date
      console.log('Watch Date',$scope.study_base_date);
      if($scope.attended.type == 'study'){
        console.log('Study Visit Type Changed: Weeks',$scope.attended.study_visit_type);
        $scope.attended.next = new Date($scope.study_base_date);
        $scope.attended.next.setDate($scope.attended.next.getDate() + $scope.attended.study_visit_type * 7);
      }
    });

    $scope.$watch('attended.type',function(newValue,oldValue) {
      // Remove automatically set study visit date
      if(oldValue == 'study') {
        $scope.attended.next = undefined;
        $scope.attended.study_visit_type = undefined;
      }
    });
  }]);

})();
