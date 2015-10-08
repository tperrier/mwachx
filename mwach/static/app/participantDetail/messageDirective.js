(function(){
  'use strict';

  var routePrefix = '/static/app/';

  angular.module('mwachx')
    .directive('mwMessage', function() {
      return {
        restrict:             'E',
        scope: {
          'message':          '=',
          'participant':      '=',
          'openSendModalFn':  '&', // This is a reference to a method from the parent controller
        },
        templateUrl:           routePrefix + 'participantDetail/messageDirective.html',
        link: function($scope, element, attrs) {
          // console.log('Message',$scope.message);
          $scope.isDisabled = function(){
            return  ($scope.message.is_pending &&
              ($scope.message.is_related === null || $scope.message.topic === ''));
          }
          $scope.dismiss = function() {
            $scope.message.doPUT($scope.message,'dismiss');
            $scope.message.is_pending = false;
          }
      }
    };
    });

})();
