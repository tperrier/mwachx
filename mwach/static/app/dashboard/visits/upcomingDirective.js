(function(){
  'use strict';

  var routePrefix = '/static/app/dashboard/visits/';

  angular.module('mwachx')
    .directive('mwUpcomingVisit',[ '$modal','mwachxUtils',function($modal,mwachxUtils) {

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
                templateUrl:routePrefix + 'attendedModal.html',
                contorller:'VisitAttendedModalController',
              });

              modalInstance.result.then(function(attended){
                console.log('Save',attended);
                attended.arrived = mwachxUtils.convert_form_date(attended.arrived);
                attended.next = mwachxUtils.convert_form_date(attended.next);
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


}());
