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

SECRET_KEY = env('SECRET_KEY')
SECRET_ADMIN_URL = env('SECRET_ADMIN_URL')

HCAPTCHA_SITEKEY = env('HCAPTCHA_SITEKEY')
HCAPTCHA_SECRET = env('HCAPTCHA_SECRET')

ALLOWED_HOSTS = ['localhost']
DEBUG = True

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

DOMAIN = "http://localhost:8000"

CSRF_TRUSTED_ORIGINS = ["http://localhost:8000"]

STATICFILES_DIRS = [
     BASE_DIR / '../assets/'
 ]