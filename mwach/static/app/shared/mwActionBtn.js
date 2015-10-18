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

          scope.get_class = function(urgency) {
            var btn_class = 'btn-info', int_urgency = parseInt(urgency,10);
            //console.log(element,urgency,urgency==undefined);
            if (int_urgency>0) {
              btn_class = 'btn-danger';
            } else if (int_urgency===0) {
              btn_class = 'btn-success';
            } else if ( !(urgency === '' || urgency === undefined) ) {
              btn_class = 'btn-'+urgency;
            }
            return btn_class;
          };
        },
      };
    });

})();
