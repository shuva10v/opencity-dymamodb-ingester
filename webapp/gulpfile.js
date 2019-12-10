const gulp = require('gulp');
const del = require('del');
const minify = require('gulp-minify');
const concat = require('gulp-concat');
const replace = require('gulp-replace');
const browserify = require('browserify');
const source = require('vinyl-source-stream');
const argv = require('yargs').argv;

gulp.task('browserify', function() {
    return browserify({
        extensions: ['.js'],
        debug: true,
        cache: {},
        packageCache: {},
        fullPaths: true,
        entries: ['./node_modules/open-location-code/openlocationcode.js',
            'main.js'
        ],
    })
        .bundle()
        .on("error", function (err) { console.log("Error : " + err.message); })
        .pipe(source('bundle.js'))
        .pipe(replace(/%%OPENCITY_API_ENDPOINT%%/g, argv.api_endpoint))
        .pipe(gulp.dest('./dist'));
});

gulp.task('minify-js', function(done) {
  gulp.src([
      'node_modules/jquery/dist/jquery.min.js',
      'node_modules/bootstrap/dist/js/bootstrap.bundle.min.js',
      'dist/bundle.js'
  ])
      .pipe(concat('app.js'))
      .pipe(minify({
        ext:{
          src:'.js',
          min:'.min.js'
        },
      }))
      .pipe(gulp.dest('dist'));
  done();
});

gulp.task('minify-css', function(done) {
    gulp.src([
        'node_modules/bootstrap/dist/css/bootstrap.min.css'])
        .pipe(concat('app.css'))
        .pipe(gulp.dest('dist'));
    done();
});

gulp.task('clean', function (done) {
    del(['.tmp', 'dist']);
    done();
})


gulp.task('default', gulp.series('clean', 'browserify', 'minify-js', 'minify-css'));