var less = require('gulp-less');
var path = require('path');
var gulp = require('gulp');
var sourcemaps = require('gulp-sourcemaps');

gulp.task('default', function() {
    gulp.src('./contacts/static/style.less')
        .pipe(sourcemaps.init())
        .pipe(less())
        .pipe(sourcemaps.write('./maps'))
        .pipe(gulp.dest('./contacts/static/css'));
});


// {
//       paths: [ path.join(__dirname, 'less', 'includes') ]
//     }
