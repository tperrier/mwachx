(function(){
  'use strict';

  var routePrefix = '/static/app/';

  // Should this be in the mwachxApp module instead since it is shared?
  angular.module('mwachx')
    .directive('mwActionBtn', function() {
      function link(scope, element, attrs) {
        element.addClass('btn action-item');
        if(scope.urgency)
          element.addClass('btn-' + scope.urgency);
      };

      return {
        restrict:     'E',
        transclude:   true,
        scope: {
          iconClass:  '=mwIcon',
          urgency:    '=mwStyle',
        },
        templateUrl:  routePrefix + '/src/shared/mwActionBtn.html',
        link:         link,
      }
    });

})();