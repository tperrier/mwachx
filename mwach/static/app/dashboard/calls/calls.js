(function(){
  'use strict';

var routePrefix = '/static/app/dashboard/calls/';

angular.module('mwachx')
  .controller('UpcomingCallsController', ['$scope','mwachxAPI',
    function ($scope, mwachxAPI) {

    mwachxAPI.pending.all('calls').getList().then(function(visits) {
      $scope.month = visits.filter(function(item,index){return item.call_type == 'm'});
      $scope.year = visits.filter(function(item,index){return item.call_type == 'y'});
    });

}]);

angular.module('mwachx') .directive('mwUpcomingCall',
  ['$modal',function($modal) {

    return {
      restrict:'A',templateUrl:routePrefix + 'callDirective.html',
      scope: {
        'call':'=',
        'callList':'=',
      },
      link: function($scope, element, attrs) {
        angular.extend($scope,{
          recordCall:function(call){
            var callModal = $modal.open({
              templateUrl: routePrefix + 'recordCallModal.html',
              size:'lg',
              controller:'RecordCallController',
              resolve:{
                resolveData:{
                  call:$scope.call,
                  callList:$scope.callList,
                }
              }
            });
          } // End RecordCall
        });
      }, // End Link
    } // End Directive Public
  }]);

angular.module('mwachx').controller('RecordCallController',
  ['$scope','$modalInstance','resolveData',
  function($scope,$modalInstance,resolveData){

    angular.extend($scope,{
      call:resolveData.call,
      new_call:{
        created:new Date(),
        comment:(resolveData.call.call_type == 'm')?'One month phone call':'One year phone call',
      },
      recordCall:function(){
        // console.log('Record',$scope.new_call);
        $scope.call.doPUT($scope.new_call,'called/').then(function(result){
          // console.log('Called',result);
          resolveData.callList.splice(resolveData.callList.indexOf($scope.call),1);
          $modalInstance.close();
        });
      },
      formDisabled:function(){
        // console.log($scope,$scope.call_form);
        return $scope.new_call.outcome === undefined || !$scope.call_form.$valid;
      }
    });

  }]);

})();
