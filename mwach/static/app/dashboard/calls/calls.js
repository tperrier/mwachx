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
  ['$modal','mwachxUtils',function($modal,mwachxUtils) {

    return {
      restrict:'A',templateUrl:routePrefix + 'callDirective.html',
      scope: {
        'call':'=',
        'callList':'=',
      },
      link: function($scope, element, attrs) {
        angular.extend($scope,{
          recordCall:function(call){
            console.log('call');
            var callModal = $modal.open({
              templateUrl: routePrefix + 'recordCallModal.html',
              size:'lg',
              controller:'RecordCallController',
              resolve:{
                call:function(){return call},
              }
            });
          } // End RecordCall
        });
      }, // End Link
    } // End Directive Public
  }]);

angular.module('mwachx').controller('RecordCallController',
  ['$scope','call',function($scope,call){
    $scope.call = call;

    $scope.add_call = function(){
      console.log($scope.new_call);
    };
  }]);

})();
