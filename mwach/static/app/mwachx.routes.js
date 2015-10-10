(function(){
  'use strict';

  var routePrefix = '/static/app/';

  // Setup the routes for the 'mwachx' module
  angular.module('mwachx')
    .config(['$stateProvider', '$urlRouterProvider',
      function($stateProvider, $urlRouterProvider) {

        // Redirect to home in case we get lost
        $urlRouterProvider.otherwise('/');

        $stateProvider
          .state('home', {
            url:          '/',
            templateUrl:  routePrefix + 'dashboard/home.html',
            controller:   'HomeController'
          })

          // Participant state and substates
          .state('participant-list', {
            url:          '/participant',
            templateUrl:  routePrefix + 'dashboard/participantList.html',
            controller:   'ParticipantListController'
          })

          .state('participant-new', {
            url:          '/participant/new',
            //templateUrl:  routePrefix + 'dashboard/participantNew.html',
            templateUrl:   'crispy-forms/participant/new',
            controller:   'ParticipantNewController'
          })
          .state('participant-details', {
            url:          '/participant/:study_id',
            templateUrl: routePrefix  + 'participantDetail/participantDetail.html',
            controller:  'ParticipantController'
          })

          // Message state and substates
          .state('messages-pending', {
            url: '/messages/pending',
            templateUrl: routePrefix + 'dashboard/messages/pendingMessages.html',
            controller: 'PendingMessageController'
          })

          // Visit state and substates
          .state('visits-upcomming', {
            url: '/visits/upcomming',
            templateUrl: routePrefix + 'dashboard/visitsUpcomming.html'
          })

          // Calls state and substates
          .state('calls',{
            url: '/calls',
            templateUrl: routePrefix + 'dashboard/calls.html'
          })

          // Translation state and substates
          .state('translations', {
            url: '/translations',
            templateUrl: routePrefix + 'dashboard/translations/pendingTranslations.html',
            controller: 'PendingTranslationController'
          })

          // Testing state
          .state('tests', {
            url: '/test',
            templateUrl: 'crispy-forms/participant/update',
            controller:'TestController'
          });
      }]);


  // *************************************
  // Basic Controller For Test Route
  // *************************************

  angular.module('mwachx')
    .controller('TestController',['$scope',
      function ($scope) {
        $scope.status = {art_initiation:false}
      }]);

})();
