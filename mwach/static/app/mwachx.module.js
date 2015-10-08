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

	.config(['showErrorsConfigProvider', function(showErrorsConfigProvider) {
    showErrorsConfigProvider.trigger('keypress');
  }])

  .config(['datepickerConfig','datepickerPopupConfig',function(datepickerConfig,datepickerPopupConfig){
    datepickerConfig.showWeeks = false;

    datepickerPopupConfig.datepickerPopup = "yyyy-MM-dd";
  }]);

})();
