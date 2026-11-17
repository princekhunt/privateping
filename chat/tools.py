import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import UserProfile
from .models import Friends

logger = logging.getLogger(__name__)


def getFriendsList(id):
    """
    Friend rows of the user, each annotated with `state`:
      "friends"  - both accepted
      "incoming" - they sent us a request we haven't answered
      "outgoing" - we sent a request they haven't answered
    """
    user = UserProfile.objects.filter(id=id).first()
    if user is None:
        return []
    rows = list(Friends.objects.filter(user=user).select_related("friend").order_by("friend__name"))
    accepted_back = set(
        Friends.objects.filter(friend=user, accepted=True).values_list("user_id", flat=True)
    )
    for row in rows:
        if not row.accepted:
            row.state = "incoming"
        elif row.friend_id in accepted_back:
            row.state = "friends"
        else:
            row.state = "outgoing"
    order = {"incoming": 0, "friends": 1, "outgoing": 2}
    rows.sort(key=lambda r: order[r.state])
    return rows


def push_to_user(username, message):
    """Sends `message` (a channels event dict) to every open page of `username`."""
    try:
        async_to_sync(get_channel_layer().group_send)("box4_" + username, message)
    except Exception:  # never fail the request because a push failed
        logger.exception("could not push %s to %s", message.get("type"), username)


def notify_friends_changed(username, event, from_user, **extra):
    """
    Pushes a "your friend list changed" event to every open page of `username`
    (over the notify websocket), so the sidebar updates without a refresh.
    """
    push_to_user(username, dict(type="friends_changed", event=event, **{"from": from_user}, **extra))


def getUserId(username):
    use = UserProfile.objects.get(username=username)
    id = use.id
    return id


def are_friends(user_a, user_b):
    """
    Returns True only if both users have accepted each other as friends.
    Accepts UserProfile instances or usernames.
    """
    try:
        if isinstance(user_a, str):
            user_a = UserProfile.objects.get(username=user_a)
        if isinstance(user_b, str):
            user_b = UserProfile.objects.get(username=user_b)
    except UserProfile.DoesNotExist:
        return False

    if user_a is None or user_b is None or user_a.pk == user_b.pk:
        return False

    return (
        Friends.objects.filter(user=user_a, friend=user_b, accepted=True).exists()
        and Friends.objects.filter(user=user_b, friend=user_a, accepted=True).exists()
    )
