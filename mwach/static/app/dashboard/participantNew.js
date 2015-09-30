(function(){
  'use strict';

  /**
   *
   * @param $scope
   * @constructor
   */
  angular.module('mwachx')
    .controller('ParticipantNewController', ['$scope','$location', function ($scope, $location) {

      $scope.status = {
        birthdate:false,
        art_initiation:false,
        due_date:false,
      };

    }]);

})();
