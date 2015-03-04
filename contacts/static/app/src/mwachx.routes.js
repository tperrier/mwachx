(function(){
  'use strict';

  var routePrefix = '/static/app/';

  // Setup the routes for the 'mwachx' module
  angular.module('mwachx')
    .config(['$routeProvider',
      function($routeProvider) {
        $routeProvider.
          when('/', {
            templateUrl: routePrefix + 'src/components/participant/participantPartial.html',
            navIndex: '0',
            controller: 'ParticipantController'
          }).
          otherwise({
            redirectTo: '/'
          });
      }]);

})();