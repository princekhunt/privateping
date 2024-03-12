import os

if os.environ.get('ENV') == 'production':
    from .production import *
else:
    from .development import *