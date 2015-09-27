(function(){
  'use strict';

  var routePrefix = '/static/app/';

  // Should this be in the mwachxApp module instead since it is shared?
  angular.module('mwachx')
    .directive('mwActionBtn', function() {

      return {
        restrict:     'E',
        transclude:   true,
        replace:      true,
        scope: {
          iconClass:  '@mwIcon',
          urgency:    '@mwStyle',
          spanClass:  '@mwStackClass',
          insideIcon: '@mwStackInside',
        },
        templateUrl: routePrefix + 'shared/mwActionBtn.html',
        link:function(scope,element,attrs){
          scope.get_count = function(urgency){
            return isNaN(parseInt(urgency))?'':parseInt(urgency); 
          }
        },
      };
    });

})();
