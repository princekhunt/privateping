from django.urls import re_path as url
from chat.consumers import (ChatConsumer, ChatConsumerCurrentStatus, ChatConsumerNotify,
                            ChatConsumerStatus)

websocket_urlpatterns = [
    # Checks the status (typing/not typing) of the user
    url(r'^ws/chat/currentstatus/$', ChatConsumerCurrentStatus.as_asgi()),

    # Check the status (online/offline) of the user
    url(r'^ws/chat/status/$', ChatConsumerStatus.as_asgi()),

    # Handle the communication between the users
    url(r'^ws/chat/$', ChatConsumer.as_asgi()),

    # Notifies a user, if any user is waiting for a chat
    url(r'^ws/notify/$', ChatConsumerNotify.as_asgi()),
]
