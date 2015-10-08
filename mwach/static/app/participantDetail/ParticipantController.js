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
            function (result) {
              // Ok button?
              $log.warn('ok button used',result,$scope.to_send);
            },
            function (reason) {
              $log.info('Send msg modal dismissed (canceled) at: ' + new Date(),reason);
          });

        };

        $scope.openModifyModel = function() {

            var modalInstance = $modal.open({
              templateUrl: routePrefix + 'modifyParticipantModal.html',
              size: 'lg',
              controller: 'ModifyParticipantController',
            });

        }

      }]);

// *************************************
// Modal Controllers
// *************************************

angular.module('mwachx')
  .controller('NewMessageController',
    function NewMessageController($scope, $modalInstance, $log) {
      angular.extend($scope,{
        // TODO: should these be fetched so we DRY?
        languageOptions:['english', 'swahili', 'sheng', 'luo'],
        languages:{},

        send:function(status) {
          var message = {
            message:$scope.message,
            languages:pri.getLanguages(),
            translation:$scope.translation,
            translation_status:status
          }
          $modalInstance.close( message );
        },

        type_message:function() {
          // Make translation track message if not changed. Angular makes this so easy!
          if($scope.send_to_form.translation.$pristine){
            $scope.translation = $scope.message;
          }
        },

        isDisabled:function(status) {
          var base_condition =  $scope.message == undefined || $scope.message == '' || pri.getLanguages() == '';
          if ( status == 'none' ) {
            return base_condition || $scope.message != $scope.translation;
          }
          else if ( status == 'done' ) {
            return base_condition || $scope.message == $scope.translation;
          }
          return base_condition;
        },

        cancel:function() {
          $modalInstance.dismiss('cancel');
        }
      });

    // *************************************
    // Private Functions
    // *************************************

    var pri = {
      getLanguages: function() {
        return Object.keys($scope.languages)
                     .filter(function(item,index){return $scope.languages[item] })
                     .join(';');
      }

    }

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
