from django.urls import re_path as url
from chat.consumers import *

websocket_urlpatterns = [

    # Checks the status ( typing/not typing) of the user
    url('ws/chat/currentstatus/', ChatConsumerCurrentStatus.as_asgi()),

    # Check the status (online/offline) of the user
    url('ws/chat/status/', ChatConsumerStatus.as_asgi()),

    # Handle the communication between the users
    url('ws/chat/', ChatConsumer.as_asgi()),

    # Notifies a user, if any user is waiting for a chat
    url('ws/notify/', ChatConsumerNotify.as_asgi()),
         ]