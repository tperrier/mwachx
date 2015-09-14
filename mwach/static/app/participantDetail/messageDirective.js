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
      };
    });

})();
