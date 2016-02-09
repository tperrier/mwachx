var less = require('gulp-less');
var path = require('path');
var gulp = require('gulp');
var sourcemaps = require('gulp-sourcemaps');
var livereload = require('gulp-livereload');
var concat = require('gulp-concat');
var uglify = require('gulp-uglify');
var plumber = require('gulp-plumber');
var os = require('os');

var webfaction_static = ( '../../' + ( (__dirname.indexOf('mwachx') >= 0)?'mwachx':'staging') + '_static')

gulp.task('test', function() {
  console.log("Filename: " + __filename);
  console.log("Directory Name: " + __dirname);
  console.log(webfaction_static);
});

gulp.task('less', function() {
    return gulp.src('./mwach/static/less/main.less')
        .pipe(plumber())
        .pipe(sourcemaps.init())
        .pipe(less())
        .pipe(sourcemaps.write('./maps'))
        .pipe(gulp.dest('./mwach/static/css'))
});

gulp.task('webfaction_less', function() {
    return gulp.src('./mwach/static/less/main.less')
        .pipe(plumber())
        .pipe(less())
        .pipe(gulp.dest(webfaction_static + '/css'))
});

// From: https://medium.com/@dickeyxxx/best-practices-for-building-angular-js-apps-266c1a4a6917
gulp.task('js',function () {
  return gulp.src(['./mwach/static/app/mwachx.module.js','mwach/static/app/**/*.js'])
    .pipe(sourcemaps.init())
      .pipe(concat('mwachx.js'))
      // .pipe(uglify())
    .pipe(sourcemaps.write('./'))
    .pipe(gulp.dest('./mwach/static'))
});

gulp.task('webfaction_js',function () {
  return gulp.src(['./mwach/static/app/mwachx.module.js','mwach/static/app/**/*.js'])
    .pipe(concat('mwachx.js'))
      // .pipe(uglify())
    .pipe(gulp.dest(webfaction_static))
});

var LIBS = [
    'mwach/static/bower_components/angular/angular.js',
    'mwach/static/bower_components/angular-ui-router/release/angular-ui-router.js',
    'mwach/static/bower_components/angular-resource/angular-resource.js',
    'mwach/static/bower_components/angular-bootstrap/ui-bootstrap-tpls.js',
    'mwach/static/bower_components/angular-bootstrap-show-errors/src/showErrors.js',
    'mwach/static/bower_components/lodash/lodash.js',
    'mwach/static/bower_components/restangular/src/restangular.js'
];

gulp.task('libs',function(){
  return gulp.src(LIBS)
   .pipe(sourcemaps.init())
    .pipe(concat('components.js'))
    .pipe(sourcemaps.write('./'))
    .pipe(gulp.dest('./mwach/static'))
});

gulp.task('webfaction_libs',function(){
  return gulp.src(LIBS)
    .pipe(concat('components.js'))
    .pipe(uglify())
    .pipe(gulp.dest(webfaction_static))
});

gulp.task('watch', function() {
	livereload.listen();
    // Recompile less -> css
    gulp.watch('**/*.less', ['less']);
    // Recompile js
    gulp.watch('mwach/static/app/**/*.js',['js']);
    /* Trigger a live reload on any Django template changes */
    gulp.watch(['**/templates/**/*.html','**views.py','**admin.py','**/*.js','**/*.html'])
      .on('change', livereload.changed);
    /* Recompile libs */
    gulp.watch('mwach/static/app/mwachx.*.js',['libs']);
});

gulp.task('default', ['watch','less','js','libs'], function() {
	return
});

gulp.task('webfaction', ['webfaction_js','webfaction_less','webfaction_libs'], function() {
  console.log('Gulp Webfaction Deploy Done');
});
