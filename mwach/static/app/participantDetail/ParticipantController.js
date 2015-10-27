(function(){
  'use strict';

// *************************************
// ParticipantController Main Controller for participants objects
// *************************************

  angular.module('mwachx') .controller('ParticipantController',
  ['$scope','$modal','$location','$stateParams','$log','$rootScope', 'Restangular',
  'mwachxAPI','mwachxUtils',
  function ParticipantController($scope, $modal, $location, $stateParams, $log, $rootScope, Restangular,
    mwachxAPI,mwachxUtils) {

    $scope.participant      = [];
    $scope.messages         = [];

    mwachxAPI.participants.get($stateParams.study_id).then(function(participant){
      $scope.participant = participant;
      $scope.messages = participant.getList('messages').$object;

      $scope.detailsList      = [
      //  {'label': 'Nickname',               'value': 'nickname',},
      //  {'label': 'Study ID',               'value': 'study_id',},
      //  {'label': 'ANC Number',             'value': 'anc_num',},
       {'label': 'Phone number',           'value': 'phone_number',},
       {'label': 'Status',                 'value': 'status_display',},
       {'label': 'Estimated Delivery Date','value': 'due_date',}
       ];

       if ( !participant.is_pregnant)
        $scope.detailsList.push({'label':'Delivery Date', 'value':'delivery_date'});

       Array.prototype.push.apply($scope.detailsList,[
         {'label': 'Age',                    'value': 'age',},
         {'label': 'Send Day',               'value': 'send_day_display',},
         {'label': 'Send Time',              'value': 'send_time_display',},
         {'label': 'SMS Track',              'value': 'condition',},
         {'label': 'ART Initiation',         'value': 'art_initiation',},
         {'label': 'Previous pregnancies',   'value': 'previous_pregnancies',},
         {'label': 'Family Planning',        'value': 'family_planning',},
         {'label': 'HIV Disclosure',         'value': 'hiv_disclosed_display',},
         {'label': 'HIV Messaging',          'value': 'hiv_messaging_display',},
       ]);

       if ( !participant.is_validated)
        $scope.detailsList.push({'label': 'Confirmation Code',      'value': 'validation_key',});
    });

    //
    // Public Methods
    //
    var routePrefix   = '/static/app/participantDetail/';
    $scope.openSendModal = function(msg) {

      var modalInstance = $modal.open({
        templateUrl: routePrefix + 'modalSendMessage.html',
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
          templateUrl: routePrefix + 'modalModifyParticipant.html',
          size: 'lg',
          controller:'ParticipantUpdateController',
          resolve:{
            participant:function(){return $scope.participant},
          },
        });

        modalInstance.result.then(function(result){
          var patch = {
            status:result.status,
            send_day:result.send_day,
            send_time:result.send_time,
            art_initiation:mwachxUtils.convert_form_date(result.art_initiation),
            hiv_disclosed:result.hiv_disclosed,
          }
          console.log('Update',result,patch);
          $scope.participant.patch(patch).then(function(result){
            console.log('PATCH',result);
            $scope.participant = result;
          });
        });

    }

    $scope.openPhoneModal = function() {

        var modalInstance = $modal.open({
          templateUrl: routePrefix + 'modalCallHistory.html',
          controller: 'PhoneCallController',
          size: 'lg',
          resolve:{
            participant:function(){return $scope.participant},
          },
        });
    }

    $scope.visitDismiss = function(visit) {
      var modalInstance = $modal.open({
        templateUrl: routePrefix + 'modalVisitDismiss.html',
        size: 'sm',
      }).result.then(function(){
        console.log('OK now dismiss',visit);
        visit.doPUT({},'skip/').then(function(response) {
          $scope.participant.visits.splice($scope.participant.visits.indexOf(visit),1);
        });
    });
  }

  $scope.scheduleVisit = function() {

    var $modalScope = $rootScope.$new(); $modalScope.scheduleOnly = true;

    var modalInstance = $modal.open({
      templateUrl: "/static/app/dashboard/visits/modalVisitAttendSchedule.html",
      scope: $modalScope,
    }).result.then(function(put) {
      console.log('Schedule',put);
      $scope.participant.post('visits/',put).then(function(response){
        $scope.participant.visits.push(
          Restangular.restangularizeElement($scope.participant,response,'visits/')
        );
      });
    });
  }

  $scope.visitAttended = function(visit) {
    var modalInstance = $modal.open({
      templateUrl: "/static/app/dashboard/visits/modalVisitAttendSchedule.html",
    }).result.then(function(attended) {
      console.log('Attended',attended);
      visit.doPUT(attended,'attended/').then(function(response){
        console.log('Result',response);
        if(response.next) {
          // There is a next visit
          $scope.participant.visits.push(
            Restangular.restangularizeElement($scope.participant,response.next,'visits/')
          );
        }
        $scope.participant.visits.splice($scope.participant.visits.indexOf(visit),1);
      });
    });
  }

  $scope.showVisitHistory = function() {
    var modalInstance = $modal.open({
      templateUrl: routePrefix + 'modalVisitHistory.html',
      controller: 'VisitHistoryModalController',
      resolve:{
        participant:function(){return $scope.participant},
      },
    });
  }

  $scope.recordDelivery = function() {

    var today = new Date().getTime();
    var $modalScope = $rootScope.$new();
    angular.extend($modalScope,{
      participant:$scope.participant,
      // 5356800000 = 62 days
      minDate: (new Date()).setTime(today - 5356800000),
      maxDate: (new Date()).setTime(today + 5356800000),
    });

    var modalInstance = $modal.open({
      templateUrl: routePrefix + 'modalDelivery.html',
      scope: $modalScope,
    }).result.then(function(delivery) {
      console.log('Delivery',delivery);
      $scope.participant.doPUT(delivery,'delivery/').then(function(result) {
        console.log('Result',result);
        if ( ! result.hasOwnProperty('error') ){
          ['status','status_display','is_pregnant','delivery_date'].forEach(function(ele) {
            $scope.participant[ele] = result[ele];
          });
        }
      });
    });
  }; // End Record Delivery

  $scope.stopMessaging = function() {

    var modalInstance = $modal.open({
      templateUrl: routePrefix + 'modalStopMessaging.html',
      size:'sm',
    });
  };

    }]); // End Main Controller

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

angular.module('mwachx').controller('ParticipantUpdateController', //Name is controlled by django form name
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
      status:{call_history_open:true},
      new_call:{is_outgoing:true,created:new Date()},
      form:{},
      addCall:function(){
        $scope.participant.post('calls/',$scope.new_call).then(function(response){
          console.log('Post Call',response,$scope.status);
          participant.calls.push(response)
          $scope.status.call_history_open = true;
          console.log($scope.status);
        });
      },
      addDisabled:function(){
        return $scope.new_call.outcome === undefined ||
               ($scope.new_call.outcome == 'answered' && $scope.form.call_form.comment.$pristine) ||
               !$scope.form.call_form.$valid;
      },
    });

  }]);


angular.module('mwachx').controller('VisitHistoryModalController',
  ['$scope','$modalInstance','$log','participant',
  function ($scope, $modalInstance, $log, participant) {
    angular.extend($scope,{
      participant: participant,
      visits: participant.all('visits').getList().$object,
    });
  }]);

})();
