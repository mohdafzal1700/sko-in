"""
Django settings for project project.

Generated by 'django-admin startproject' using Django 5.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os  # For accessing environment variables
from dotenv import load_dotenv
import os
from django.urls import reverse_lazy

dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path)




# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-*eax6t8-*p4a=sw-kv*nd2sdno#f36_kk(^c&_n-3^o#1gs%f@'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition
SITE_ID=2

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'User_side',
    'Sko_Adminside',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google'
    
    
]


SOCIALACCOUNT_PROVIDERS = {
     'google': {
        'APP': {
            'client_id': '893024725251-slj6gt01ug1csbesjigp5teo1a9k81vj.apps.googleusercontent.com',
            'secret': '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',
            'key': ''
        },  
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'Sko_Adminside.middleware.AdminAccessMiddleware'
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR/'templates'],
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

WSGI_APPLICATION = 'project.wsgi.application'


DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10 MB (You can adjust this value as needed)

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'backend',
        'USER': 'mysuperuser',
        'PASSWORD': 'mysuperuser',
        'HOST': 'backend.czo628m24sbu.ap-southeast-2.rds.amazonaws.com',
        'PORT': '5432',
    }
}


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'skodata',      # Database name
#         'USER': 'postgres',           # PostgreSQL username
#         'PASSWORD': 'afsal',   # PostgreSQL password
#         'HOST': 'localhost',        # Host address (default is localhost)
#         'PORT': '5432',             # Default PostgreSQL port
#     }
# }




# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'  # This is where Django will serve static files.

STATICFILES_DIRS = [
    os.path.join(BASE_DIR,'User_side/static')# Optional: If you have a global static folder.
]

STATIC_ROOT = BASE_DIR / 'static'  # For production, when you collect all static files.


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Example for Gmail
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER =" skoin347@gmail.com"
EMAIL_HOST_PASSWORD =" tcwu bntw vkzk cyty"


AUTHENTICATION_BACKENDS= (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend"
    
)


LOGIN_REDIRECT_URL = reverse_lazy('home')
LOGOUT_REDIRECT_URL="/"


# Use the custom social account adapter
SOCIALACCOUNT_ADAPTER = 'User_side.adapters.CustomSocialAccountAdapter'

# Razorpay API keys (not secure for production)
RAZOR_API_KEY = "rzp_test_KDYrLJHnu3O9Ip" 
RAZOR_SECRET_ID  = "bcOjtnHN19lrbqBWdS35Ee7J"


# Admin side session configuration
SESSION_COOKIE_NAME = 'Sko_Adminside_sessionid'

# User side session configuration
USER_SESSION_COOKIE_NAME = 'User_side_sessionid'


DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = 'AKIAR3HUODVIUM3BQVHG'
AWS_SECRET_ACCESS_KEY = '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'
AWS_STORAGE_BUCKET_NAME = 'skodin'
AWS_S3_SIGNATURE_NAME = 's3v4',
AWS_S3_REGION_NAME = 'ap-southeast-2'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL =  None
AWS_S3_VERITY = True
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'        
