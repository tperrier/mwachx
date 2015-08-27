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
          iconClass:  '=mwIcon',
          urgency:    '=mwStyle',
          spanClass:  '=mwStackClass',
          insideIcon: '=mwStackInside',
        },
        templateUrl:  getTemplate,
      };

      function isAnchor(attr) {
        return angular.isDefined(attr.href) || angular.isDefined(attr.ngHref);
      }

      function getTemplate(element, attr) {
        return isAnchor(attr) ?
               routePrefix + 'shared/mwActionBtnAnchor.html':
               routePrefix + 'shared/mwActionBtnLabel.html';
      }

    });

})();
