(function() {
  'use strict';

angular.module('mwachx')
  .factory('mwachxUtils',['$filter',function($filter){
    var service = {};

    service.convert_form_date = function(date) {
      return $filter('date')(date,'yyyy-MM-dd');
    };

    return service;
  }]);

// *************************************
// Directive for making DIV's editable
// *************************************
angular.module('mwachx')
.directive("contenteditable", function() {
  return {
    restrict: "A",
    require: "ngModel",
    link: function(scope, element, attrs, ngModel) {

      function read() {
        ngModel.$setViewValue(element.html());
      }

      ngModel.$render = function() {
        element.html(ngModel.$viewValue || "");
      };

      element.bind("blur keyup change", function() {
        scope.$apply(read);
      });
    }
  };
})

// *************************************
// Filter to capitalize first letter: from
// *************************************
angular.module('mwachx')
.filter('capitalize', function() {
  return function(input, scope) {
    if (input!=null)
    input = input.toLowerCase();
    return input.substring(0,1).toUpperCase()+input.substring(1);
  }
});

})();
