import json
import re

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from chat import cooldown
from chat.models import UserProfile
from chat.tools import are_friends
from registration.security import TokenBucket

# Allowed self-destruct timers (seconds). 0 = do not destroy.
ALLOWED_DESTROY = {0, 5, 10, 30, 60, 300, 600, 3600}
# Messages are an opaque, end-to-end encrypted envelope (see assets/js/crypto.js).
MAX_MESSAGE_LEN = 16 * 1024
MAX_FRAME_LEN = MAX_MESSAGE_LEN + 512
MAX_USERNAME_LEN = 20
MAX_RECEIPT_LEN = 8 * 1024
MID_RE = re.compile(r"[0-9a-f]{32}")
TYPING_STATUSES = ("online", "typing")


def _valid_username(value):
    return isinstance(value, str) and 0 < len(value) <= MAX_USERNAME_LEN


def _profile(username):
    try:
        return UserProfile.objects.get(username=username)
    except UserProfile.DoesNotExist:
        return None


def _parse(text_data):
    """Parses a client frame; returns a dict or None."""
    if not isinstance(text_data, str) or len(text_data) > MAX_FRAME_LEN:
        return None
    try:
        data = json.loads(text_data)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


class AuthenticatedConsumer(WebsocketConsumer):
    """Base class: rejects anonymous sockets, joins a per-user group and rate limits frames."""
    group_prefix = None
    rate = 5      # frames per second (sustained)
    burst = 20    # frames allowed in a burst

    def connect(self):
        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            self.close()
            return
        self.username = user.username
        self.room_name = self.group_prefix + self.username
        self.bucket = TokenBucket(self.rate, self.burst)
        async_to_sync(self.channel_layer.group_add)(self.room_name, self.channel_name)
        self.accept()
        self.on_connect()

    def on_connect(self):
        pass

    def receive(self, text_data=None, bytes_data=None):
        if not getattr(self, "username", None):
            self.close()
            return
        if not self.bucket.allow():
            return  # silently drop floods
        data = _parse(text_data)
        if data is None:
            self.on_invalid()
            return
        self.handle(data)

    def on_invalid(self):
        pass

    def handle(self, data):
        raise NotImplementedError

    def disconnect(self, code):
        if getattr(self, "room_name", None):
            async_to_sync(self.channel_layer.group_discard)(self.room_name, self.channel_name)


class ChatConsumer(AuthenticatedConsumer):
    """
    Relays end-to-end encrypted messages, delivery receipts and presence between two *friends*.
    The server never sees plaintext; it only checks that sender and recipient are friends.

    Client -> server frames:
      {"message": <encrypted envelope>, "to": <user>, "destroy": <s>, "mid": <32 hex>}
          -> server answers {"status": "accepted", "mid": ...} ("sent" tick) or an error
      {"receipt": <signed receipt JSON>, "to": <user>}   delivered / read receipts (signed by
                                                        the recipient, verified by the sender)
      {"ready": true|false, "to": <user>}               "my chat page is live" - lets the other
                                                        side resend anything not yet delivered
      {"message": "ping", ...}                          -> {"message": "pong"}
    """
    group_prefix = "box_"
    rate = 10
    burst = 60   # retries + receipts after a reconnect come in bursts

    def on_connect(self):
        UserProfile.objects.filter(username=self.username).update(online=1)

    def _error(self, reason="Invalid message", mid=None):
        payload = {'message': reason, 'status': "error", 'destroy': 0}
        if mid:
            payload['mid'] = mid
        self.send(text_data=json.dumps(payload))

    def on_invalid(self):
        self._error()

    def _relay(self, to, event):
        event['from'] = self.username
        async_to_sync(self.channel_layer.group_send)("box_" + to, event)

    def handle(self, data):
        to = data.get('to')
        if not _valid_username(to):
            self._error()
            return

        # --- presence ------------------------------------------------------
        if 'ready' in data:
            if are_friends(self.username, to):
                self._relay(to, {'type': 'chat_ready', 'reply': bool(data.get('ready') is False)})
            return

        # --- receipts ------------------------------------------------------
        if 'receipt' in data:
            receipt = data.get('receipt')
            if not isinstance(receipt, str) or not receipt or len(receipt) > MAX_RECEIPT_LEN:
                self._error()
                return
            if are_friends(self.username, to):
                self._relay(to, {'type': 'chat_receipt', 'receipt': receipt})
            return

        # --- messages ------------------------------------------------------
        message = data.get('message')
        mid = data.get('mid')
        try:
            destroy = int(data.get('destroy', 0))
        except (TypeError, ValueError):
            destroy = 0
        if destroy not in ALLOWED_DESTROY:
            destroy = 0

        if not isinstance(message, str) or not message or len(message) > MAX_MESSAGE_LEN:
            self._error()
            return

        if message == "ping":
            self.send(text_data=json.dumps({'message': "pong", 'status': "received", 'destroy': destroy}))
            return

        if not isinstance(mid, str) or not MID_RE.fullmatch(mid):
            self._error()
            return

        # Only relay messages between mutually accepted friends.
        if not are_friends(self.username, to):
            self._error("You can only message friends.", mid=mid)
            return

        self._relay(to, {'type': 'chat_message', 'message': message, 'destroy': destroy, 'mid': mid})
        # "Sent": the server accepted the message. Delivery is only ever confirmed by the
        # recipient's signed receipt - the server can't know whether anyone received it.
        self.send(text_data=json.dumps({'status': 'accepted', 'mid': mid}))

    def chat_message(self, event):
        self.send(text_data=json.dumps({
            'message': event['message'],
            'status': "received",
            'destroy': event['destroy'],
            'mid': event.get('mid', ''),
            'from': event.get('from', ''),
        }))

    def chat_receipt(self, event):
        self.send(text_data=json.dumps({'status': 'receipt', 'receipt': event['receipt'],
                                        'from': event.get('from', '')}))

    def chat_ready(self, event):
        self.send(text_data=json.dumps({'status': 'ready', 'reply': event.get('reply', False),
                                        'from': event.get('from', '')}))

    def disconnect(self, code):
        super().disconnect(code)
        if getattr(self, "username", None):
            UserProfile.objects.filter(username=self.username).update(online=0, online_for=None)


class ChatConsumerStatus(AuthenticatedConsumer):
    """
    Online status of a friend: {"check": "livestatus", "for": <username>}.
    Replies 'offline' to the caller, or notifies the friend that we're online
    when the friend is online *and* in a chat with us.
    """
    group_prefix = "box2_"

    def handle(self, data):
        if data.get('check') != "livestatus":
            return
        for_user = data.get('for')
        if not _valid_username(for_user):
            return
        for_profile = _profile(for_user)
        me = _profile(self.username)
        if (for_profile is not None and me is not None and are_friends(me, for_profile)
                and for_profile.online == 1 and for_profile.online_for_id == me.pk):
            async_to_sync(self.channel_layer.group_send)(
                "box2_" + for_user,
                {'type': 'UserLiveStatus', 'status': 'online', 'user': for_user}
            )
        else:
            self.send(text_data=json.dumps({'status': 'offline', 'user': for_user}))

    def UserLiveStatus(self, event):
        self.send(text_data=json.dumps({'status': event['status'], 'user': event['user']}))


class ChatConsumerCurrentStatus(AuthenticatedConsumer):
    """
    Typing indicator / "I'm in a chat with X": {"status": "typing"|"online", "for": <username>}.
    Only friends can mark themselves as waiting for / typing to someone.
    """
    group_prefix = "box3_"
    rate = 10
    burst = 30

    def handle(self, data):
        for_user = data.get('for')
        status = data.get('status')
        if for_user == "NULL" or not _valid_username(for_user) or status not in TYPING_STATUSES:
            return
        me = _profile(self.username)
        for_profile = _profile(for_user)
        if me is None or for_profile is None or not are_friends(me, for_profile):
            return
        # Recently declined: don't ping them again until the cool-down ends
        # (unless they are the one waiting for us).
        if (me.online_for_id != for_profile.pk and for_profile.online_for_id != me.pk
                and cooldown.remaining("chat", me.username, for_profile.username)):
            return
        if me.online_for_id != for_profile.pk:
            me.online_for = for_profile
            me.save(update_fields=["online_for"])

        async_to_sync(self.channel_layer.group_send)(
            "box3_" + for_user,
            {'type': 'In_chat_message', 'status': status, 'user': for_user, 'from': self.username}
        )

    def In_chat_message(self, event):
        self.send(text_data=json.dumps({
            'status': event['status'], 'user': event['user'], 'from': event.get('from', '')
        }))


class ChatConsumerNotify(AuthenticatedConsumer):
    """
    Tells the user which friends are waiting for them: {"available": "ping"}.
    Replies {"status": "notify", "from": "[...usernames]"} or {"status": "no"}.
    """
    group_prefix = "box4_"

    def handle(self, data):
        if data.get('available') != "ping":
            return
        me = _profile(self.username)
        if me is None:
            return
        waiting = (UserProfile.objects.filter(online=1, online_for=me)
                   .exclude(username=self.username))
        avl_users = [p.username for p in waiting if are_friends(me, p)]
        if avl_users:
            self.send(text_data=json.dumps({'status': 'notify', 'from': json.dumps(avl_users)}))
        else:
            self.send(text_data=json.dumps({'status': 'no', 'from': 'NULL'}))

    def friends_changed(self, event):
        """Server push: this user's friend list changed (request / accepted / rejected / removed)."""
        payload = {'status': 'friends', 'event': event.get('event', ''), 'from': event.get('from', '')}
        if event.get('retry_in'):
            payload.update(retry_in=event['retry_in'], retry_text=event.get('retry_text', ''))
        self.send(text_data=json.dumps(payload))

    def chat_declined(self, event):
        """Server push: the friend we were waiting for declined the chat."""
        self.send(text_data=json.dumps({
            'status': 'declined', 'from': event.get('from', ''),
            'retry_in': event.get('retry_in', 0), 'retry_text': event.get('retry_text', ''),
        }))
