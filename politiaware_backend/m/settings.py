import os
from pathlib import Path

from politiaware_backend.conf.conf_loader import config

django_conf = config["django"]

# Determine the environment file to load
from dotenv import load_dotenv
ENV_FILE = os.getenv("ENV_FILE", ".env")
load_dotenv(ENV_FILE)

# Get the SECRET_KEY from the .env file
SECRET_KEY = os.getenv('SECRET_KEY','fallback-secret-key')

# Set DEBUG mode from .env
DEBUG = os.getenv('DEBUG', 'True')

# Allowed Hosts
'''
CORS_ALLOWED_ORIGINS = [
'http://localhost:4200',
'https://www.adhikar.net',
'http://localhost:8100/',
'*',

]'''
CORS_ALLOW_ALL_ORIGINS = True
#ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
ALLOWED_HOSTS = django_conf.get('allowed_hosts', '').split(',') if django_conf.get('allowed_hosts') else []

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!




# Application definition

INSTALLED_APPS = [
    'django_crontab',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'crispy_forms',
    'import_export',    
    'embed_video',
    'phonenumber_field',
    'rest_framework.authtoken',
    'django_rest_passwordreset',
    'django_filters',
     "cloudinary",
    "cloudinary_storage",
     'party',  
     'debug_toolbar',
     'drf_spectacular', 
     'person',
     "graphene_django",    
     'dbbackup',  
     'django.contrib.gis',
     'state',
     'district',
     'city',
     'governor',
     'cm',
     'loksabha',
     'rajyasabha',
     'assembly',
     'council',
     'session_info',
]

GRAPHENE = {
    "SCHEMA": "django_root.schema.schema"
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
     'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    "debug_toolbar.middleware.DebugToolbarMiddleware",


]

ROOT_URLCONF = 'm.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'm.wsgi.application'
ASGI_APPLICATION = 'm.asgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases




# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

IMPORT_EXPORT_USE_TRANSACTIONS = True



#AUTHENTICATION_BACKENDS = ['n.authentication.EmailBackend']


STATIC_URL = '/static/'
STATIC_ROOT = '/static/'
'''STATIC_ROOT = os.path.join(BASE_DIR, '')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]'''

MEDIA_URL = '/images/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'images')

DEFAULT_THROTTLE_CLASSES = [
    'rest_framework.throttling.UserRateThrottle',
    'rest_framework.throttling.AnonRateThrottle',
]
DEFAULT_THROTTLE_RATES = {
    'user': '1000/day',
    'anon': '100/minute',
}




try :
    from .db_settings import *    
except ImportError:
    pass
