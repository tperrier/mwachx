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

  .config(['$urlMatcherFactoryProvider',function($urlMatcherFactoryProvider){
    // $uiViewScrollProvider.useAnchorScroll();
    $urlMatcherFactoryProvider.strictMode(false)
  }])

	.config(['showErrorsConfigProvider', function(showErrorsConfigProvider) {
    showErrorsConfigProvider.trigger('keypress');
  }])

  .config(['datepickerConfig','datepickerPopupConfig',function(datepickerConfig,datepickerPopupConfig){
    datepickerConfig.showWeeks = false;

    datepickerPopupConfig.datepickerPopup = "yyyy-MM-dd";
    datepickerPopupConfig.closeText = 'Cancel';
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
        change_facility:function(){
          console.log('Change',$scope.facility);
          $http.get('staff/facility_change/'+$scope.facility).then(function(response){
            $state.reload();
            console.log(response);
          });
        },
      });

      var pri = {
        delta_date:function(direction,delta){
          $http.get('staff/date/'+direction+'/'+delta+'/').then(function(response){
            // $state.transitionTo('home',null,{reload:true});
            $state.reload();
            $scope.current_date = response.data.current_date;
          });
        },
      }
    }]);


})();
