"""
Django settings for _base project.

Generated by 'django-admin startproject' using Django 4.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from pathlib import Path
import os

from dotenv import find_dotenv, load_dotenv


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# load environment vars
load_dotenv(find_dotenv())


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-#a9jhxfs6rc_q$u%hdlp1=&ye2b0z_0^fw&4fuy_@n59%q@$cv'

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['*']

DEBUG = True


# Application definition

INSTALLED_APPS = [
    # user defined apps
    'core.apps.CoreConfig',
    'users.apps.UsersConfig',
    'listings.apps.ListingsConfig',
    'subscriptions.apps.SubscriptionsConfig',
    'payments.apps.PaymentsConfig',
    # 'services.apps.ServicesConfig',
    # 'search.apps.SearchConfig',
    'auths.apps.AuthsConfig',
    'messaging.apps.MessagingConfig',
    # 'bookings.apps.BookingsConfig',


    # third party apps
    'django_htmx',


    # built in apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # third party middle ware
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = '_base.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        # project level template organization
        'DIRS': [
            BASE_DIR / 'templates',
        ],

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

WSGI_APPLICATION = '_base.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME")
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
MEDIA_ROOT = 'media/'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'

# added for file pythonanywhere deployment
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---> custom settings <---

# custom auth model
AUTH_USER_MODEL = "users.User"

AUTHENTICATION_BACKENDS = [
    # added for email based auth
    'auths.backends.EmailBackend'
]

LOGIN_URL = "login"
LOGOUT_REDIRECT_URL = 'login'

# celery settings
CELERY_BROKER_URL = os.getenv('REDIS_URL')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL')

# Email Creds
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587  # or 465 if using SSL
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')


# settings.py


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} -> {module} -> {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'django_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, '_logs', 'django.log'),
            'formatter': 'verbose',
        },
        'generic_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, '_logs', '_generic.log'),
            'formatter': 'verbose',
        },
        'auths_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, '_logs', 'auths.log'),
            'formatter': 'verbose',
        },
        'core_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, '_logs', 'core.log'),
            'formatter': 'verbose',
        },
        'listings_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, '_logs', 'listings.log'),
            'formatter': 'verbose',
        },
        'messaging_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, '_logs', 'messaging.log'),
            'formatter': 'verbose',
        },
        'payments_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, '_logs', 'payments.log'),
            'formatter': 'verbose',
        },
        'subscriptions_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, '_logs', 'subscriptions.log'),
            'formatter': 'verbose',
        },
        'users_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, '_logs', 'users.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['django_file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'auths': {
            'handlers': ['auths_file', 'generic_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'core': {
            'handlers': ['core_file', 'generic_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'listings': {
            'handlers': ['listings_file', 'generic_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'messaging': {
            'handlers': ['messaging_file', 'generic_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'payments': {
            'handlers': ['payments_file', 'generic_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'subscriptions': {
            'handlers': ['subscriptions_file', 'generic_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'users': {
            'handlers': ['users_file', 'generic_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}


##### Modify progressively #####
# redirects users to login for routes with login required
"""

LOGIN_REDIRECT_URL = "get_customer_dashboard_fragment"

# LOGOUT_REDIRECT_URL = 'login'



# Google Creds
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

# Facebbok creds
FACEBOOK_CLIENT_ID = os.getenv('FACEBOOK_CLIENT_ID')
FACEBOOK_CLIENT_SECRET = os.getenv('FACEBOOK_CLIENT_SECRET')
FB_AUTHORIZATION_BASE_URL = "https://www.facebook.com/dialog/oauth"
FB_TOKEN_URL = "https://graph.facebook.com/oauth/access_token"
FB_SCOPE = ['email']

# AWS S3 settings
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = "prbucket01"
AWS_S3_REGION_NAME = 'eu-west-2'
AWS_QUERYSTRING_AUTH = False

# S3 static settings
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
# STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

# S3 media settings
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'


# STRIPE
STRIPE_PUBLIC_KEY_TEST = os.getenv('STRIPE_PUBLIC_KEY_TEST')
STRIPE_SECRET_KEY_TEST = os.getenv('STRIPE_SECRET_KEY_TEST')
STRIPE_WEBHOOK_SECRET_TEST = os.getenv('STRIPE_WEBHOOK_SECRET_KEY_TEST')

REDIRECT_DOMAIN = os.getenv('HOME_URL')

 """
