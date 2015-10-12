(function(){
  'use strict';

  // Prepare the 'mwachx' module for subsequent registration of controllers and delegates
  angular.module('mwachx', [ 'ui.bootstrap', 'ui.bootstrap.showErrors', 'ui.router',
    'ngResource','restangular'])
  	.config(['$resourceProvider', '$httpProvider','RestangularProvider',
    function($resourceProvider, $httpProvider,RestangularProvider) {
	  // Don't strip trailing slashes from calculated URLs
	  $resourceProvider.defaults.stripTrailingSlashes = false;
	  $httpProvider.defaults.xsrfCookieName = 'csrftoken';
	  $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';

    RestangularProvider.setBaseUrl('/api/v0.1/');
    RestangularProvider.setRequestSuffix("\/");

	}])

  .config(['$uiViewScrollProvider',function($uiViewScrollProvider){
    // $uiViewScrollProvider.useAnchorScroll();
  }])

	.config(['showErrorsConfigProvider', function(showErrorsConfigProvider) {
    showErrorsConfigProvider.trigger('keypress');
  }])

  .config(['datepickerConfig','datepickerPopupConfig',function(datepickerConfig,datepickerPopupConfig){
    datepickerConfig.showWeeks = false;

    datepickerPopupConfig.datepickerPopup = "yyyy-MM-dd";
  }]);

// *************************************
// mwachx MainController
// *************************************

  angular.module('mwachx').controller("MainController",
    ['$scope','$state','$http','$filter',function($scope,$state,$http,$filter) {

      angular.extend($scope,{
        date_forward:function(delta){
          delta = delta || 1;
          pri.delta_date('forward',delta);
        },
        date_backward:function(delta){
          delta = delta || 1;
          pri.delta_date('back',delta);
        },
      });

      var pri = {
        delta_date:function(direction,delta){
          $http.get('staff/date/'+direction+'/'+delta+'/').then(function(response){
            // $state.transitionTo('home',null,{reload:true});
            $state.reload();

            // Update $scope.current_date
            delta *= (direction == 'back')?-1:1;
            var epoch = new Date( Date.parse($scope.current_date) + (86400*delta*1000) );
            $scope.current_date = $filter('date')(epoch,'yyyy-MM-dd','UTC');
            console.log(delta,epoch,$scope.current_date);
          });
        },
      }
    }]);


})();
