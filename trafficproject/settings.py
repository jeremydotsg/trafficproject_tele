"""
Django settings for trafficproject project.

Generated by 'django-admin startproject' using Django 5.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""
from pathlib import Path
import logging
import pytz
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

# Set the logging level to DEBUG
logging.basicConfig(level=logging.DEBUG)

STATIC_URL = "static/"
# Build paths inside the project like this: BASE_DIR / 'subdir'.
if os.getenv('ENVIRONMENT') in ['prod']:
    BASE_DIR = Path(__file__).resolve().parent.parent
    STATIC_URL = os.getenv('STATIC')
    STATIC_ROOT = os.getenv('STATIC_ROOT')
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
    #STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
    STATIC_URL = os.getenv('STATIC', '/static/')
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
    
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# Environment
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

CSRF_TRUSTED_ORIGINS = [
    'https://jam-app.koyeb.app',
    'http://jam-app.koyeb.app',
    'http://jam-app.koyeb.app:8000',
    'https://jam-app.koyeb.app:8000',
    'http://trafficproject-koyeb.jem-app.internal:8000'
]

CORS_ALLOWED_ORIGINS = [
    'https://jam-app.koyeb.app',
    'http://jam-app.koyeb.app',
    'http://jam-app.koyeb.app:8000',
    'https://jam-app.koyeb.app:8000',
    'http://trafficproject-koyeb.jem-app.internal:8000'
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_USE_SESSIONS = True

#Keys
SECRET_KEY = os.getenv('SECRET_KEY', '')
RECAPTCHA_PUBLIC_KEY = os.getenv('RECAPTCHA_PUBLIC_KEY', '')
RECAPTCHA_PRIVATE_KEY = os.getenv('RECAPTCHA_PRIVATE_KEY', '')

# Application definition

INSTALLED_APPS = [
    'trafficdb.apps.TrafficdbConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_recaptcha',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'trafficdb.middleware.BlockNonLocalMiddleware',
]

ROOT_URLCONF = 'trafficproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
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

WSGI_APPLICATION = 'trafficproject.wsgi.application'

#Logging
#Logging of application

class AsiaSingaporeFormatter(logging.Formatter):
    def converter(self, timestamp):
        dt = datetime.fromtimestamp(timestamp)  # Corrected usage
        tz = pytz.timezone('Asia/Singapore')
        return dt.astimezone(tz)

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return dt.isoformat()


#Logging
LOG_BASE_PATH = os.getenv('LOG_BASE_PATH', '')

LOG_INFO_FILENAME = os.path.join(LOG_BASE_PATH, 'info.log')
LOG_APP_FILENAME = os.path.join(LOG_BASE_PATH, 'app.log')
LOG_MIDDLEWARE_FILENAME = os.path.join(LOG_BASE_PATH, 'middleware.log')

# log_directories = [os.path.dirname(LOG_INFO_FILENAME), os.path.dirname(LOG_APP_FILENAME), os.path.dirname(LOG_MIDDLEWARE_FILENAME)]
#
# for directory in log_directories:
#     if not os.path.exists(directory):
#         os.makedirs(directory)
#         print(directory)


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',  # Set the desired log level
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'trafficdb': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'trafficdb_middleware': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}




# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases


if os.getenv('ENVIRONMENT') == 'prod':
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('PROD_DB_ENGINE'),
            'NAME': os.getenv('PROD_DB_NAME'),
            'USER': os.getenv('PROD_DB_USER'),
            'PASSWORD': os.getenv('PROD_DB_PASSWORD'),
            'HOST': os.getenv('PROD_DB_HOST'),
            'PORT': os.getenv('PROD_DB_PORT'),
        }
    }
elif os.getenv('ENVIRONMENT') == 'prod_koyeb' and os.getenv('PERSIST_DB') == "True":
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('PROD_DB_ENGINE'),
            'NAME': os.getenv('PROD_DB_NAME'),
            'USER': os.getenv('PROD_DB_USER'),
            'PASSWORD': os.getenv('PROD_DB_PASSWORD'),
            'HOST': os.getenv('PROD_DB_HOST'),
            'OPTIONS': {'sslmode': 'require'},
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('DEV_DB_ENGINE', 'django.db.backends.sqlite3'),
            'NAME': os.path.join(BASE_DIR, os.getenv('DEV_DB_NAME', 'db.sqlite3')),
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Singapore'

USE_I18N = True

USE_TZ = True




# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


RECAPTCHA_REQUIRED_SCORE = os.getenv('RECAPTCHA_REQUIRED_SCORE')
