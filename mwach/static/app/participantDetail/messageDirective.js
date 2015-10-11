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
          if ($scope.message.translation_status == 'done') {
            $scope.message.show_translation = true;
          }

          $scope.isDisabled = function(){
            return  ($scope.message.is_pending &&
              ($scope.message.is_related === null || $scope.message.topic === ''));
          }

          $scope.dismiss = function() {
            $scope.message.doPUT($scope.message,'dismiss').then(function(result){
              $scope.message.is_pending = false;
            });
          }

          $scope.retranslate = function() {
            console.log('retranslate');
            $scope.message.doPUT($scope.message,'retranslate').then(function(result){
              $scope.message.translation_status = 'todo';
            });
          }
      }
    };
    });

})();
