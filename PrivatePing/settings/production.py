from .base import *

import os
import sentry_sdk
import dj_database_url
import django_heroku

django_heroku.settings(locals())


SECRET_KEY = os.environ.get('SECRET_KEY')
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
DEBUG = False
ALLOWED_HOSTS = ['privateping.bytespot.tech', 'dev.privateping.bytespot.tech']

HCAPTCHA_SITEKEY = os.environ.get('HCAPTCHA_SITEKEY')
HCAPTCHA_SECRET = os.environ.get('HCAPTCHA_SECRET')

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
            "hosts": [os.environ.get('REDIS_URL')],
            "symmetric_encryption_keys": [SECRET_KEY],
        },
    }
}

DATABASES = {}
DATABASES['default'] = dj_database_url.config(conn_max_age=600)
DATABASES['default']['CONN_MAX_AGE'] = 60

STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

STATICFILES_DIRS = [
    BASE_DIR / '../assets/static'
]
STATIC_ROOT = BASE_DIR / '../assets/'

DISABLE_SERVER_SIDE_CURSORS = True

DOMAIN = "https://privateping.bytespot.tech"