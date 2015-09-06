var less = require('gulp-less');
var path = require('path');
var gulp = require('gulp');
var sourcemaps = require('gulp-sourcemaps');
var livereload = require('gulp-livereload');
var concat = require('gulp-concat')

gulp.task('less', function() {
    gulp.src('./mwach/static/less/main.less')
        .pipe(sourcemaps.init())
        .pipe(less())
        .pipe(sourcemaps.write('./maps'))
        .pipe(gulp.dest('./mwach/static/css'))
        .pipe(livereload());
});

// From: https://medium.com/@dickeyxxx/best-practices-for-building-angular-js-apps-266c1a4a6917
gulp.task('js',function () {
  gulp.src(['./mwach/static/app/mwachx.module.js','mwach/static/app/**/*.js'])
    .pipe(sourcemaps.init())
      .pipe(concat('mwachx.js'))
    .pipe(sourcemaps.write('./'))
    .pipe(gulp.dest('./mwach/static'))
})

gulp.task('watch', function() {
	livereload.listen();
    gulp.watch('**/*.less', ['less']);
    /* Trigger a live reload on any Django template changes */
    gulp.watch('**/templates/**/*.html').on('change', livereload.changed);
    gulp.watch('**views.py').on('change', livereload.changed);
    gulp.watch('**admin.py').on('change', livereload.changed);
    gulp.watch('**/*.js').on('change', livereload.changed);
    gulp.watch('**/*.html').on('change', livereload.changed);
});

gulp.task('default', ['less', 'watch'], function() {
	return
});
