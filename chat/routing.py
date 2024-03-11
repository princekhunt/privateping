from django.urls import re_path as url
from chat.consumers import ChatConsumer

websocket_urlpatterns = [
    url('ws/chat', ChatConsumer.as_asgi())
         ]