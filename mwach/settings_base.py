"""
Django settings for mwach project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
#Determain if we are running on OpenShift
ON_OPENSHIFT = True if os.environ.has_key('OPENSHIFT_REPO_DIR') else False

# The top directory for this project. Contains requirements/, manage.py,
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

# The directory with this project's templates, settings, urls, static dir,
# wsgi.py, fixtures, etc.
PROJECT_PATH = os.path.join(PROJECT_ROOT, 'mwach')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'a638cezc!olqzorlxr_@kq#z5+3(v8c&31by99i$nh+o3x=jkt'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TEMPLATE_DEBUG = True
ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admindocs',

    'crispy_forms',
    'rest_framework',

    #constane setup
    'constance',
    'constance.backends.database',

    # Transports
    'transports',

    #mWaChx setup
    'contacts',
    'backend',
    'utils',

    # tests
    'django_nose',
)

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    # 'PAGINATE_BY': 10
}


CRISPY_TEMPLATE_PACK = 'bootstrap3'

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.debug',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.core.context_processors.i18n',
    'django.core.context_processors.static',

    'constance.context_processors.config',

    'utils.context_processors.current_date',
    'utils.context_processors.brand_status',
)

ROOT_URLCONF = 'mwach.urls'
WSGI_APPLICATION = 'wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases
SQLITE_DB_FOLDER = os.environ['OPENSHIFT_DATA_DIR'] if ON_OPENSHIFT else PROJECT_PATH
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(SQLITE_DB_FOLDER, 'mwach.db'),
   }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
DATE_INPUT_FORMATS = ('%d-%m-%Y','%Y-%m-%d')
USE_I18N = False
USE_L10N = False
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(PROJECT_ROOT,'static')
if ON_OPENSHIFT:
    STATIC_ROOT = os.path.join(os.environ.get('OPENSHIFT_REPO_DIR'),'wsgi','static')

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

STATICFILES_DIRS = (
    os.path.join(PROJECT_PATH,'static'),
)

#CONSTANCE SETUP
CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
CONSTANCE_CONFIG = {
    'CURRENT_DATE':('2015-8-1','Current Date for training'),
}

################
# Logging
################
LOGGING_DIR = os.environ['OPENSHIFT_DATA_DIR'] if ON_OPENSHIFT else PROJECT_PATH
LOGGING =   {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mwach_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR,'mwach.log'),
            'formatter':'basic',
        },
        'console': {
            'level':'DEBUG',
            'class':'logging.StreamHandler',
        },
    },
     'formatters': {
        'basic': {
           'format': '%(asctime)s %(name)-20s %(levelname)-8s %(message)s',
        },
    },
    'loggers': {
        'africas_talking': {
            'handlers':['mwach_file'],
            'level':'DEBUG',
            'propagate':True,
        },
    },
}

#############
# Custom Settings
#############
MESSAGING_CONTACT = 'contacts.Contact'
MESSAGING_CONNECTION = 'contacts.Connection'
MESSAGING_ADMIN = 'auth.User'

FACILITY_CHOICES = (
    ('mathare','Mathare'),
    ('bondo','Bondo'),
    ('ahero','Ahero'),
    ('siaya','Siaya'),
    ('rachuonyo','Rachuonyo'),
    ('riruta','Riruta'),
)
