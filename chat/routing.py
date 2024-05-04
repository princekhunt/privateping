from django.urls import re_path as url
from chat.consumers import ChatConsumer, ChatConsumerStatus, ChatConsumerCurrentStatus

websocket_urlpatterns = [
    url('ws/chat/currentstatus/', ChatConsumerCurrentStatus.as_asgi()),
    url('ws/chat/status/', ChatConsumerStatus.as_asgi()),
    url('ws/chat/', ChatConsumer.as_asgi()),
         ]