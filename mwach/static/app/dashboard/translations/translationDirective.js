(function(){
  'use strict';

  var routePrefix = '/static/app/dashboard/translations/';

  angular.module('mwachx')
    .directive('mwTranslation', function() {

      var pri = {
        getLanguages: function($scope) {
          return Object.keys($scope.languages)
                       .filter(function(item,index){return $scope.languages[item] })
                       .join(';');
        }
      }; // close private


      return {
        restrict:             'A',
        scope: {
          'message':          '=',
          'pending':          '=',
        },
        templateUrl:           routePrefix + 'translationDirective.html',
        link: function($scope, element, attrs) {

          // Set default translated text
          if (!$scope.message.translated_text) {
            $scope.message.translated_text = $scope.message.text;
          }

          angular.extend($scope,{
            languageOptions:{'e':'english', 's':'swahili', 'h':'sheng', 'l':'luo'},
            languages:{},
            isDisabled:function(translate){
              var base = pri.getLanguages($scope) == '';
              if (translate == 'translate') {
                base = base || ($scope.message.text == $scope.message.translated_text);
              }
              return base;
            },
            translate:function(status){
              var put = {
                text:$scope.message.translated_text,
                status:status,
                languages:pri.getLanguages($scope),
              };
              $scope.message.doPUT(put,'translate').then(function(result){
                // Remove element from pending translation list
                console.log('Translate',result);
                $scope.pending.splice($scope.pending.indexOf($scope.message),1);
              });
            }
          });

        }
      }
    });

}());
