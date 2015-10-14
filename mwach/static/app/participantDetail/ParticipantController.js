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
        $scope.openSendModal = function(msg) {

          var modalInstance = $modal.open({
            templateUrl: routePrefix + 'newMessageModal.html',
            controller: 'NewMessageController',
            size: 'lg',
            resolve: {
              reply:function(){
                if(msg) {
                  return msg;
                }
              }
            }
          });

          modalInstance.result.then(
            function (result) {
              $log.warn(result.type+' button used',result);
              if (result.reply !== undefined) {
                // filter out extra pramaters on reply
                var oldReply = result.reply;
                result.reply = {
                  id:oldReply.id,
                  is_related:oldReply.is_related,
                  topic:oldReply.topic,
                }
              }
              $scope.participant.post('messages/',result).then(function(result){
                console.log('Post Message',result);
                if( oldReply !== undefined) {oldReply.is_pending = false;}
                $scope.messages.push(result);
              });
            },
            function (reason) {
              $log.info('Send msg modal dismissed (canceled) at: ' + new Date(),reason);
          });

        };

        $scope.openModifyModel = function() {

            var modalInstance = $modal.open({
              templateUrl: routePrefix + 'modifyParticipantModal.html',
              size: 'lg',
              controller:'ParticipantUpdateController',
              resolve:{
                participant:function(){return $scope.participant},
              },
            });

            modalInstance.result.then(function(result){
              console.log('Update',result);
            });

        }

        $scope.openPhoneModal = function() {

            var modalInstance = $modal.open({
              templateUrl: routePrefix + 'phoneCallModal.html',
              size: 'lg',
              controller: 'PhoneCallController',
              resolve:{
                participant:function(){return $scope.participant},
              },
            });
        }

      }]);

// *************************************
// Modal Controllers
// *************************************

angular.module('mwachx') .controller('NewMessageController',
  ['$scope','$modalInstance','$log','reply',
  function ($scope, $modalInstance, $log, reply) {
    angular.extend($scope,{
      // TODO: should these be fetched so we DRY?
      languageOptions:['english', 'swahili', 'sheng', 'luo'],
      languages:{},
      reply:reply,

      send:function(status) {
        console.log('Send',$scope.reply);
        var message = {
          message:$scope.message,
          languages:pri.getLanguages(),
          translated_text:$scope.translation,
          translation_status:status,
        }
        if (reply !== undefined ) {
          message.reply = reply;
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

}]);

angular.module('mwachx') .controller('ParticipantUpdateController', //Name is controlled by django form name
  ['$scope','$modalInstance','$log','participant',
  function ($scope, $modalInstance, $log, participant) {
    angular.extend($scope,{
        participant:participant,
    });
  }]);

angular.module('mwachx') .controller('PhoneCallController',
  ['$scope','$modalInstance','$log','participant',
  function ($scope, $modalInstance, $log, participant) {
    angular.extend($scope,{
        participant:participant,
        new_call:{incoming:false,created:new Date()},
        add_call:function(){
          $scope.participant.post('calls/',$scope.new_call).then(function(response){
            console.log('Post Call');
          });
        },
    });
  }]);

})();
