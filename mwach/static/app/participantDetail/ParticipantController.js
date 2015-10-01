(function(){
  'use strict';

// *************************************
// ParticipantController Main Controller for participants objects
// *************************************

  angular.module('mwachx')
    .controller('ParticipantController',['$scope','$modal','$location','$stateParams','$log','$rootScope',
      'mwachxAPI',
      function ParticipantController($scope, $modal, $location, $stateParams, $log, $rootScope,
        mwachxAPI) {

        $scope.participant      = [];
        $scope.messages         = [];

        mwachxAPI.participants.get($stateParams.study_id).then(function(participant){
          $scope.participant = participant;
          $scope.messages = participant.getList('messages').$object;
        });

        $scope.detailsList      = [
         {'label': 'Nickname',               'value': 'nickname',},
         {'label': 'Study ID',               'value': 'study_id',},
         {'label': 'ANC Number',             'value': 'anc_num',},
         {'label': 'Phone number',           'value': 'phone_number',},
         {'label': 'Status',                 'value': 'status',},
         {'label': 'Estimated Delivery Date','value': 'phone_number',},
         {'label': 'Send Day',               'value': 'send_day',},
         {'label': 'Send Time',              'value': 'send_time',},
         {'label': 'SMS Track',              'value': 'condition',},
         {'label': 'ART Initiation',         'value': 'art_initiation',},
         {'label': 'Previous pregnancies',   'value': 'previous_pregnancies',},
         {'label': 'Family Planning',        'value': 'family_planning',},
         {'label': 'HIV Disclosure',         'value': 'hiv_disclosed',},
         {'label': 'Confirmation Code',      'value': 'validation_key',},
        ];

        //
        // Public Methods
        //
        var routePrefix   = '/static/app/participantDetail/';
        $scope.openSendModal = function(origMsg) {

          var modalScope    = $rootScope.$new();
          modalScope.params = {origMsg: origMsg};

          var modalInstance = $modal.open({
            templateUrl: routePrefix + 'newMessageModal.html',
            controller: 'NewMessageController',
            size: 'lg',
            scope: modalScope
          });

          modalInstance.result.then(
            function () {
              // Ok button?
              $log.warn('ok button used');
            },
            function () {
              $log.info('Send msg modal dismissed (canceled) at: ' + new Date());
          });

        };

        $scope.openModifyModel = function() {

            var modalInstance = $modal.open({
              templateUrl: routePrefix + 'modifyParticipantModal.html',
              size: 'lg',
              controller: 'ModifyParticipantController',
            });

        }
        //
        // Private Methods
        //

        var isDisabled = function(i) {
          return (this.is_pending && (typeof this.related === 'undefined' || this.topic === 'none'));
        }

      }]);

// *************************************
// Modal Controllers
// *************************************

    angular.module('mwachx')
      .controller('NewMessageController',
        function NewMessageController($scope, $modalInstance, $log) {

          // Vars
          // TODO: should these be fetched so we DRY?
          $scope.languageOptions  = ['English', 'Swahili', 'Sheng', 'Luo'];
          $scope.languages        = new Set(); // Using some advanced stuff because we control our user's browser

          // Methods for close and cancel
          $scope.ok = function() {
            $modalInstance.close(
              // In here goes anything I want to pass back
              );
          };
          $scope.cancel = function() {
            $modalInstance.dismiss('cancel');
          };
      });

    angular.module('mwachx').controller('ModifyParticipantController',
      ['$scope','$modalInstance',
        function ($scope,$modalInstance) {

          // Methods for close and cancel
          $scope.ok = function() {
            $modalInstance.close(
              // In here goes anything I want to pass back
              );
          };
          $scope.cancel = function() {
            $modalInstance.dismiss('cancel');
          };
        }]);


})();
