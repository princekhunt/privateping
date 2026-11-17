from .base import *
import os
import sentry_sdk
import dj_database_url

DEBUG = False

SECRET_KEY = os.environ['SECRET_KEY']  # fail fast if missing
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
ALLOWED_HOSTS = ['privateping.apps.princekhunt.com']
SECRET_ADMIN_URL = os.environ['SECRET_ADMIN_URL']


#security config
SECURE_HSTS_SECONDS = 63072000  # 2 years
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_NAME = "__Host-sessionid"
CSRF_COOKIE_NAME = "__Host-csrftoken"
CSRF_TRUSTED_ORIGINS = ["https://privateping.apps.princekhunt.com"]
TRUST_X_FORWARDED_FOR = True  # Heroku router appends the real client IP
SECURE_HSTS_PRELOAD = True

#sentry config
SENTRY_DSN = os.environ.get('SENTRY_DSN')
sentry_sdk.init(
    dsn=SENTRY_DSN,
    traces_sample_rate=1.0,
    send_default_pii=False,
)

#cache (rate limiting) - shared across dynos
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get('REDIS_URL'),
    }
}

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
# (previously configured by the abandoned django-heroku package)
DATABASES = {"default": dj_database_url.config(conn_max_age=60, conn_health_checks=True, ssl_require=True)}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {"django": {"handlers": ["console"], "level": "INFO", "propagate": False}},
}

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

STATICFILES_DIRS = [
    BASE_DIR / '../assets/static'
]
STATIC_ROOT = BASE_DIR / '../assets/'

DISABLE_SERVER_SIDE_CURSORS = True

DOMAIN = "https://privateping.apps.princekhunt.com"