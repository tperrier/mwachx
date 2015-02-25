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
    'parsley',
    
    #constane setup
    'constance',
    'constance.backends.database',
    
    #mWaChx setup
    'contacts',
    'utils',
    'http_transport',
    'africas_talking',
)

CRISPY_TEMPLATE_PACK = 'bootstrap3'

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
    
    'utils.context_processors.openshift',
    'utils.context_processors.current_date',
    'utils.context_processors.brand_status',
)

ROOT_URLCONF = 'mwach.urls'

WSGI_APPLICATION = 'wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases
SQLITE_DB_FOLDER = os.environ['OPENSHIFT_DATA_DIR'] if ON_OPENSHIFT else PROJECT_PATH

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
if ON_OPENSHIFT:
    STATIC_ROOT = os.path.join(os.environ.get('OPENSHIFT_REPO_DIR'),'wsgi','static')
else:
    STATIC_ROOT = os.path.join(PROJECT_ROOT, STATIC_URL.strip("/"))


# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

#CONSTANCE SETUP
CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'

CONSTANCE_CONFIG = {
    'CURRENT_DATE':('2014-8-1','Current Date for training'),
    'AFRICAS_TALKING_SEND':(False,"Africa's Talking Send"),
}

#############
# Custom Settings
#############

MESSAGING_CONTACT = 'contacts.Contact'
MESSAGING_CONNECTION = 'contacts.Connection'
MESSAGING_ADMIN = 'auth.User'

try:
    from local_settings import *
except ImportError as e:
    #Silently fail if no local settings 
    pass
