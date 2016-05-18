(function(){
  'use strict';

  /**
   * Main Controller for participants objects?
   * @param $scope
   * @constructor
   */
  angular.module('mwachx').controller('ParticipantListController',
  ['$scope','$stateParams','mwachxAPI','mwParticipantFilterService',
  function ($scope, $stateParams, mwachxAPI,participantService) {

      $scope.query = participantService.query;

      var query_functions = {
        study_group:{
          control:function(participant){ return participant.study_group == 'Control'},
          one_way:function(participant){ return participant.study_group == 'One Way'},
          two_way:function(participant){ return participant.study_group == 'Two Way'},
        },
        status:{
            pregnant:function(participant){ return participant.status == 'Pregnant'},
            post_partum:function(participant){ return participant.status == 'Post-Partum'},
            other:function(participant){ return participant.status !== 'Pregnant' && participant.status !== 'Post-Partum'},
        }
      };

      var compare_participant = function(participant,cmp) {
        if(cmp == 'text') {
          var needle = $scope.query.text.toLowerCase();
          return [participant.study_id,participant.nickname,participant.anc_num,participant.phone_number].some(
            function(value){
              return value.toLowerCase().indexOf(needle) >= 0;
          }
          );
        } else {
          var result = false, once = false;
          angular.forEach($scope.query[cmp], function(value,key) {
            if(value === true && result === false) {
              once = true;
              if ( query_functions[cmp][key](participant) ) {
                result = true;
              }
            }
          })
          return result || !once;
        }
      }

      $scope.participantFilter = function(participant) {

          var filter_buttons = ['study_group','status'].every( function(query) {
            return compare_participant(participant,query);
          })
          var filter_text = compare_participant(participant,'text');

          if ($scope.query.text == '') {
            return filter_buttons;
          } else {
            return filter_text || (filter_buttons && filter_text);
          }
      }

      $scope.setSort = function(sortName) {
        if ($scope.query.sortName == sortName) {
          $scope.query.sortDirection ^= 1; // inplace xor flips sortDirection
        }
        $scope.query.sortName = sortName;
      }

      $scope.participants = mwachxAPI.participants.getList().$object;
      if ($stateParams.message) $scope.alerts = [$stateParams.message];
      $scope.closeAlert = function(i){$scope.alerts.splice(i,1)}
    }]);

})();
