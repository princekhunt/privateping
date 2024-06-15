import os

if os.environ.get('DJANGO_ENV') == 'production':
    from .production import *
else:
    from .development import *