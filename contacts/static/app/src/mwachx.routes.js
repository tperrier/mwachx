(function(){
  'use strict';

  var routePrefix = '/static/app/';

  // Setup the routes for the 'mwachx' module
  angular.module('mwachx')
    .config(['$routeProvider',
      function($routeProvider) {
        $routeProvider.
          when('/', {
            templateUrl: routePrefix + 'src/components/participant/participantListPartial.html',
            controller:  'ParticipantListController'
          }).
          when('/new/', {
            templateUrl: routePrefix + 'src/components/participant/participantNewPartial.html',
            controller:  'ParticipantNewController'
          })
          .when('/:study_id', {
            templateUrl: routePrefix + 'src/components/participant/participantPartial.html',
            controller:  'ParticipantController'
          }).
          otherwise({
            redirectTo: '/'
          });
      }]);

})();