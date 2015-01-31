var less = require('gulp-less');
var path = require('path');
var gulp = require('gulp');
var sourcemaps = require('gulp-sourcemaps');
var livereload = require('gulp-livereload');

gulp.task('less', function() {
    gulp.src('./contacts/static/style.less')
        .pipe(sourcemaps.init())
        .pipe(less())
        .pipe(sourcemaps.write('./maps'))
        .pipe(gulp.dest('./contacts/static/css'))
        .pipe(livereload());
});

gulp.task('watch', function() {
	livereload.listen();
    gulp.watch('./contacts/static/**/*.less', ['less']);
    /* Trigger a live reload on any Django template changes */
    gulp.watch('**/templates/*').on('change', livereload.changed);
});

gulp.task('default', ['less', 'watch'], function() {
	return
});