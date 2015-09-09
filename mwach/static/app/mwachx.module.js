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
	}])
	.config(['showErrorsConfigProvider', function(showErrorsConfigProvider) {
  showErrorsConfigProvider.trigger('keypress');
}]);

})();
