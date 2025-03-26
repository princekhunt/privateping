from .base import *
import os
import sentry_sdk
import dj_database_url
import django_heroku

django_heroku.settings(locals())

DEBUG = False

SECRET_KEY = os.environ.get('SECRET_KEY')
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
ALLOWED_HOSTS = ['privateping.apps.princekhunt.com']
SECRET_ADMIN_URL = os.environ.get('SECRET_ADMIN_URL')

#hcaptcha config
HCAPTCHA_SITEKEY = os.environ.get('HCAPTCHA_SITEKEY')
HCAPTCHA_SECRET = os.environ.get('HCAPTCHA_SECRET')

#security config
SECURE_HSTS_SECONDS = 60
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_HSTS_PRELOAD = True

#sentry config
SENTRY_DSN = os.environ.get('SENTRY_DSN')
sentry_sdk.init(
    dsn=SENTRY_DSN,
    enable_tracing=True,
)

#channels config
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get('REDIS_URL')],
            "symmetric_encryption_keys": [SECRET_KEY],
        },
    }
}

#database config
DATABASES = {}
DATABASES['default'] = dj_database_url.config(conn_max_age=600)
DATABASES['default']['CONN_MAX_AGE'] = 60

STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

STATICFILES_DIRS = [
    BASE_DIR / '../assets/static'
]
STATIC_ROOT = BASE_DIR / '../assets/'

DISABLE_SERVER_SIDE_CURSORS = True

DOMAIN = "https://privateping.apps.princekhunt.com"