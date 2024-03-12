from .base import *

import os
import sentry_sdk


SECRET_KEY = os.environ.get('SECRET_KEY')
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
DEBUG = False
ALLOWED_HOSTS = ['privateping.plutoweb.live']


SECURE_HSTS_SECONDS = 60
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_HSTS_PRELOAD = True

SECRET_ADMIN_URL = os.environ.get('SECRET_ADMIN_URL')
SENTRY_DSN = os.environ.get('SENTRY_DSN')

sentry_sdk.init(
    dsn=SENTRY_DSN,
    enable_tracing=True,
)

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": os.environ.get('REDIS_URL'),
            "symmetric_encryption_keys": [SECRET_KEY],
        },
    }
}

DATABASES ={
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT')
    }
}