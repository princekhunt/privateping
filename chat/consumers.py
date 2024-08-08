import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from chat.models import UserProfile

class ChatConsumer(WebsocketConsumer):
    """
    Description: This consumer is used to send and receive messages between two users.
    A user will send a message ('message') along with the username ('to') of friend to send the message to the friend, also the user will send a message ('destroy') to destroy the message.
        'destroy' contains seconds after which the message will be destroyed.
    If the friend is online, the message will be sent to the friend and the user will receive a message with status 'received'.
    """
    http_user_and_session = True
    def connect(self):
        user = self.scope["user"]
        
        # If user is not authenticated, close the connection.
        if not user.is_authenticated:
            self.close()
            return
        
        # handle the case where the user might not exist
        try:
            UpdateStatus = UserProfile.objects.get(username=user)
            UpdateStatus.online = 1
            UpdateStatus.save()
        except UserProfile.DoesNotExist:
            self.close()
            return
        
        self.room_name = "box_"+str(user)
        async_to_sync(self.channel_layer.group_add)(
            self.room_name,
            self.channel_name
        )
        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        # handle cases where the input might not be valid JSON
        try:
            text_data_json = json.loads(text_data)
        except json.JSONDecodeError:
            self.send(text_data=json.dumps({
                'message': "Invalid JSON",
                'status': "error",
                'destroy': 0
            }))
            return
        
        message = text_data_json['message']
        to = text_data_json['to']
        destroy = text_data_json['destroy']
        
        # checks to ensure message, to, and destroy are present and valid
        if not message or not to or isinstance(destroy, int):
            self.send(text_data=json.dumps({
                'message': "Invalid JSON",
                'status': "error",
                'destroy': 0
            }))
            return

        if message == "ping":
            self.send(text_data=json.dumps({
                'message': "pong",
                'status': "received",
                'destroy': destroy
            }))
            return

        async_to_sync(self.channel_layer.group_send)(
            "box_"+str(to),
            {
                'type': 'chat_message',
                'message': message,
                'destroy': destroy
            }
        )   

    def chat_message(self, event):
        self.send(text_data=json.dumps({
            'message': event['message'],
            'status': "received",
            'destroy': event['destroy']
        }))


    def disconnect(self, code):
        user = self.scope["user"]
        '''
        # handle the case where the user might not exist
        # handle the case where the user might not exist in the UserProfile model during the disconnect process. 
        # This is to ensure that the user is removed from the online list when they disconnect.
        '''
        try:
            UpdateStatus = UserProfile.objects.get(username=user)
            UpdateStatus.online = 0
            UpdateStatus.online_for = None
            UpdateStatus.save()
        except UserProfile.DoesNotExist:
            pass
        self.close()


class ChatConsumerStatus(WebsocketConsumer):
    """
    Description: This consumer is used to check the online status of the user.
    A user will send a message ('check') along with the username ('for') of friend to check the online status of the friend.
    If the friend is online, the user will receive a message with status 'online' and vice versa.
    """
    http_user_and_session = True
    def connect(self):
        user = self.scope["user"]
        self.room_name = "box2_"+str(user)
        async_to_sync(self.channel_layer.group_add)(
            self.room_name,
            self.channel_name
        )
        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)

        if text_data_json['check']=="livestatus":
            ForUser = text_data_json['for']
            user = self.scope["user"]
            if UserProfile.objects.get(username=ForUser).online==1 and UserProfile.objects.get(username=ForUser).online_for==UserProfile.objects.get(username=user):
                async_to_sync(self.channel_layer.group_send)(
                    "box2_"+str(ForUser),
                    {
                        'type': 'UserLiveStatus',
                        'status': 'online',
                        'user': ForUser
                    }
                )
            else:
                self.send(text_data=json.dumps({
                    'status': 'offline',
                    'user': ForUser
                }))

    def UserLiveStatus(self, event):
        status = event['status']
        user = event['user']
        self.send(text_data=json.dumps({
            'status': status,
            'user': user
        }))

    def disconnect(self, code):
        self.close()

class ChatConsumerCurrentStatus(WebsocketConsumer):
    """
    Description: This consumer is used to check the current status of the user (typing/not typing).
    A user will send a message ('status') along with the username ('for') of friend to check the current status of the friend.
    If the friend is typing, the user will receive a message with status 'typing' otherwise 'online'.
    """
    http_user_and_session = True
    def connect(self):
        user = self.scope["user"]
        self.room_name = "box3_"+str(user)
        async_to_sync(self.channel_layer.group_add)(
            self.room_name,
            self.channel_name
        )
        self.accept()


    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)

        if text_data_json['for'] != "NULL":
            status = text_data_json['status']
            ForUser = text_data_json['for']
            user = self.scope["user"]
            UserUpdate = UserProfile.objects.get(username=user)
            UserUpdate.online_for = UserProfile.objects.get(username=ForUser)
            UserUpdate.save()

            async_to_sync(self.channel_layer.group_send)(
                "box3_"+str(ForUser),
                {
                    'type': 'In_chat_message',
                    'status': status,
                    'user': ForUser
                }
            )

    def In_chat_message(self, event):
        status = event['status']
        user = event['user']
        self.send(text_data=json.dumps({
            'status': status,
            'user': user
        }))

    def disconnect(self, code):
        self.close()


class ChatConsumerNotify(WebsocketConsumer):
    """
    Description: This consumer is used to notify the user, if anyone is in waiting room, waiting for the user to come online.
    A user will receive a message with status 'notify' along with the username ('from') of friend who sent the message.
    """
    http_user_and_session = True
    def connect(self):
        user = self.scope["user"]
        self.room_name = "box4_"+str(user)
        async_to_sync(self.channel_layer.group_add)(
            self.room_name,
            self.channel_name
        )
        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)

        if text_data_json['available']=="ping":
            user = self.scope["user"]
            if UserProfile.objects.filter(online=1).filter(online_for=UserProfile.objects.get(username=user)).exclude(username=user).exists():
                all = UserProfile.objects.filter(online=1).filter(online_for=UserProfile.objects.get(username=user)).exclude(username=user)
                avl_users = []
                for i in all:
                    avl_users.append(i.username)
                if len(avl_users)>0:
                    avl_users = json.dumps(avl_users)
                    async_to_sync(self.channel_layer.group_send)(
                        "box4_"+str(user),
                        {
                            'type': 'NotifyUser',
                            'status': 'notify',
                            'from': avl_users
                        }
                    )
                else:
                    self.send(text_data=json.dumps({
                        'status': 'no',
                        'from': 'NULL'
                    }))
            else:
                self.send(text_data=json.dumps({
                    'status': 'no',
                    'from': 'NULL'
                }))
    def NotifyUser(self, event):
        status = event['status']
        from_user = event['from']
        self.send(text_data=json.dumps({
            'status': status,
            'from': from_user
        }))

    def disconnect(self, code):
        self.close()