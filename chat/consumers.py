import json
from json.decoder import JSONDecodeError
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from chat.models import Keys, UserProfile
from channels.db import database_sync_to_async
import time

class ChatConsumer(WebsocketConsumer):


    http_user_and_session = True
    def connect(self):
        user = self.scope["user"]
        
        UpdateStatus = UserProfile.objects.get(username=user)
        UpdateStatus.online = 1

        UpdateStatus.save()

        self.room_name = "box_"+str(user)

        async_to_sync(self.channel_layer.group_add)(
            self.room_name,
            self.channel_name
        )
        self.accept()




    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.dumps(text_data)
        text_data_json = json.loads(text_data)

        try:
            #Check User's online status
            if text_data_json['check']=="livestatus":
                ForUser = text_data_json['for']
                user = self.scope["user"]
                #requested user's userprofile
                if UserProfile.objects.get(username=ForUser).online==1 and UserProfile.objects.get(username=ForUser).online_for==UserProfile.objects.get(username=user):
                    async_to_sync(self.channel_layer.group_send)(
                        "box_"+str(ForUser),
                        {
                            'type': 'UserLiveStatus',
                            'status': 'online',
                            'user': ForUser
                        }
                    )
                else:
                    self.send(text_data=json.dumps({
                        'status': "offline",
                        'user': ForUser
                    }))

        except Exception as e:
            pass


        try:
            if text_data_json['status'] == "online" and text_data_json['for']!="NULL":
                ForUser = text_data_json['for']
                user = self.scope["user"]
                UserUpdate = UserProfile.objects.get(username=user)
                UserUpdate.online_for = UserProfile.objects.get(username=ForUser)
                UserUpdate.save()
            #end here
        except Exception as e:
            pass
        
        try:
            if text_data_json['status'] == "typing" and text_data_json['for']!="NULL":
                ForUser = text_data_json['for']
                user = self.scope["user"]
                
                async_to_sync(self.channel_layer.group_send)(
                    "box_"+str(ForUser),
                    {
                        'type': 'In_chat_message',
                        'status': 'typing',
                        'user': ForUser
                    }
                )
        except Exception as e:
            pass

        try:
            message = text_data_json['message']

            to = text_data_json['to']

            async_to_sync(self.channel_layer.group_send)(
                "box_"+str(to),
                {
                    'type': 'chat_message',
                    'message': message
                }
            )   

        except Exception as e:
                pass

        try:
            if text_data_json['status'] == "online" and text_data_json['for']!="NULL":
                ForUser = text_data_json['for']
                user = self.scope["user"]
                
                async_to_sync(self.channel_layer.group_send)(
                    "box_"+str(ForUser),
                    {
                        'type': 'In_chat_message',
                        'status': 'online',
                        'user': ForUser
                    }
                )
        except Exception as e:
            pass

    def chat_message(self, event):
        try:
            message = event['message']
            self.send(text_data=json.dumps({
                'message': message,
                'status': "received"
            }))
        except:
            pass

    def In_chat_message(self, event):

        type = event['type']
        status = event['status']
        user = event['user']
        self.send(text_data=json.dumps({
            'status': status,
            'user': user
        }))

    def UserLiveStatus(self, event):
        status = event['status']
        user = event['user']
        self.send(text_data=json.dumps({
            'status': status,
            'user': user
        }))

    def disconnect(self, code):
        user = self.scope["user"]
        try:

            UpdateStatus = UserProfile.objects.get(username=user)
            UpdateStatus.online = 0

            UpdateStatus.online_for = None

            UpdateStatus.save()

        except:
            pass

        pass