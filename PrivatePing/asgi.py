import os

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PrivatePing.settings')
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    # Reject websocket handshakes whose Origin is not one of ALLOWED_HOSTS
    # (prevents cross-site WebSocket hijacking with the victim's session cookie).
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
    "http": get_asgi_application()
})
