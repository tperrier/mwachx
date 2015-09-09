(function(){
  'use strict';

  /**
   * Main Controller for participants objects?
   * @param $scope
   * @constructor
   */
  angular.module('mwachx')
    .controller('ParticipantController',['$scope','$modal','$location','$stateParams','$log','$rootScope',
      'mwachxAPI',
      function ParticipantController($scope, $modal, $location, $stateParams, $log, $rootScope,
        mwachxAPI) {


        $scope.openSendModal    = openSendModal;
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
        function openSendModal(origMsg) {

          var routePrefix   = '/static/app/components/new-msg-modal/';
          var modalScope    = $rootScope.$new();
          modalScope.params = {origMsg: origMsg};

          var modalInstance = $modal.open({
            templateUrl: routePrefix + 'newMessageModal.html',
            controller: 'NewMessageController',
            size: 'lg',
            scope: modalScope,
            resolve: {
              items: function () {
                return $scope.items;
              }
            }
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

        //
        // Private Methods
        //

        var isDisabled = function(i) {
          return (this.is_pending && (typeof this.related === 'undefined' || this.topic === 'none'));
        }

      }]);

})();
