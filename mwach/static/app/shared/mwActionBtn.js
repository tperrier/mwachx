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
            return isNaN(parseInt(urgency))?'':urgency;
          };
          scope.get_class = function(urgency) {
            var btn_class = 'btn-info';
            if (urgency !== '') {
              console.log(element,urgency,urgency==0);
              if (isNaN(parseInt(urgency))) {
                btn_class = 'btn-'+urgency;
              } else if (urgency>0) {
                btn_class = 'btn-danger';
              } else if (urgency==0) {
                btn_class = 'btn-success';
              }
              element.addClass(btn_class);
              return btn_class;
            }
          };
        },
      };
    });

})();
