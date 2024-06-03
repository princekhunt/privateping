from .base import *
import environ

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

env = environ.Env()
environ.Env.read_env()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

SECRET_KEY = env('SECRET_KEY')
SECRET_ADMIN_URL = env('SECRET_ADMIN_URL')
ALLOWED_HOSTS = ['127.0.0.1']
DEBUG = False

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

DOMAIN = "http://127.0.0.1:8000"

CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:8000"]