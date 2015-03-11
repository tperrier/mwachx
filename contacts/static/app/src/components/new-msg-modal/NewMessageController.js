(function(){
  'use strict';

  /**
   * Modal Controller for writing new messages
   * @param $scope
   * @param $modalInstance
   * @constructor
   */
  angular.module('mwachx')
    .controller('NewMessageController', 
      function ParticipantController($scope, $modalInstance, $log) {

        // Vars
        // TODO: should these be fetched so we DRY?
        $scope.languageOptions  = ['English', 'Swahili', 'Sheng', 'Luo']; 
        $scope.languages        = new Set(); // Using some advanced stuff because we control our user's browser
        
        // Methods
        $scope.ok               = ok;
        $scope.cancel           = cancel;

        // 
        // Public Methods
        //
        function ok() {
          $modalInstance.close(
            // In here goes anything I want to pass back 
            );
        };
        function cancel() {
          $modalInstance.dismiss('cancel');
        };
    });

})();