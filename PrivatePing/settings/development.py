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


ALLOWED_HOSTS = ['localhost', '127.0.0.1']
DEBUG = env.bool('DEBUG', default=True)

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
}

DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

DOMAIN = "http://localhost:8000"

CSRF_TRUSTED_ORIGINS = ["http://localhost:8000", "http://127.0.0.1:8000"]

STATICFILES_DIRS = [
     BASE_DIR / '../assets/'
 ]