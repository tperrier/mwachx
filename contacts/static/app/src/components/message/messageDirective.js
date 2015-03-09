(function(){
  'use strict';

  var routePrefix = '/static/app/';

  angular.module('mwachx')
    .directive('mwMessage', function() {
      return {
        restrict:     'E',
        scope: {
          'message':  '=',
        },
        templateUrl:  routePrefix + 'src/components/message/messageDirective.html',
      };
    });

})();