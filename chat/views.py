import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_safe, require_http_methods, require_POST

from chat import cooldown
from chat.models import Friends, Keys, UserProfile
from chat.tools import are_friends, getFriendsList, notify_friends_changed, push_to_user
from registration.models import user_type
from registration.security import check_and_hit


def _is_anonymous_account(user):
    return user_type.objects.filter(user=user, type="Anonymous").exists()


def _base_context(request, profile, **extra):
    """Context shared by every page that extends chat/Base.html."""
    context = {
        "friends": getFriendsList(profile.id),
        "anonymous": _is_anonymous_account(request.user),
        "curr_user": profile,
    }
    context.update(extra)
    return context


def _profile_or_none(user):
    return UserProfile.objects.filter(user=user).first()


@login_required
@require_safe
def index(request):
    """Dashboard: friend list + greeting."""
    profile = _profile_or_none(request.user)
    if profile is None:
        return redirect("registration:logout")
    return render(request, "chat/Base.html", _base_context(request, profile))


@login_required
@require_http_methods(["GET", "POST"])
def addFriend(request, name):
    """
    Sends a friend request to the user `name`.
    GET shows a confirmation page; only a POST (with a CSRF token) creates the request,
    so a third-party page or link cannot make a user send friend requests silently.
    """
    current_user = _profile_or_none(request.user)
    friend = UserProfile.objects.filter(username=name).first()
    if current_user is None:
        return redirect("registration:logout")
    if friend is None:
        messages.error(request, "No user with that username exists.")
        return redirect("chat:dashboard")
    if friend.pk == current_user.pk:
        messages.info(request, "You can't add yourself as a friend.")
        return redirect("chat:dashboard")

    source = request.POST if request.method == "POST" else request.GET
    note = source.get("note", "").strip()
    if len(note) > 100:
        messages.error(request, "The note can be at most 100 characters.")
        return redirect("chat:dashboard")

    if Friends.objects.filter(user=current_user, friend=friend).exists() or \
            Friends.objects.filter(user=friend, friend=current_user).exists():
        if are_friends(current_user, friend):
            messages.info(request, f"You and {friend.username} are already friends.")
        else:
            messages.info(request, f"A friend request between you and {friend.username} is already pending.")
        return redirect("chat:dashboard")

    wait = cooldown.remaining("friend", current_user.username, friend.username)
    if wait:
        messages.warning(request, f"{friend.username} declined your last request. "
                                  f"You can send another one in {cooldown.humanize(wait)}.")
        return redirect("chat:dashboard")

    if request.method != "POST":
        return render(request, "chat/AddFriendConfirm.html",
                      _base_context(request, current_user, target=friend, note=note))

    if check_and_hit("friend-request", current_user.pk, limit=20, window=3600):
        messages.error(request, "You're sending friend requests too quickly. Please try again later.")
        return redirect("chat:dashboard")

    # The sender's side is accepted; the receiver has to accept explicitly.
    Friends.objects.create(user=current_user, friend=friend, accepted=True)
    Friends.objects.create(user=friend, friend=current_user, note=note, accepted=False)
    notify_friends_changed(friend.username, "request", current_user.username)

    messages.success(request, f"Friend request sent to {friend.username}.")
    return redirect("chat:dashboard")


@login_required
@require_safe
def chat(request, username):
    """
    Chat page with `username`. Only mutually accepted friends can open it, and only
    then is the friend's public key handed out.
    """
    curr_user = _profile_or_none(request.user)
    friend = UserProfile.objects.filter(username=username).first()
    if curr_user is None or friend is None or not are_friends(curr_user, friend):
        messages.error(request, "You can only chat with friends who accepted your request.")
        return redirect("chat:dashboard")

    key = Keys.objects.filter(user=friend).first()
    if key is None or not key.public_key or not key.signing_key:
        messages.warning(request, f"{friend.username} needs to log in again before you can chat securely.")
        return redirect("chat:dashboard")

    try:
        friend_keys = {"enc": json.loads(key.public_key), "sig": json.loads(key.signing_key)}
    except json.JSONDecodeError:
        messages.error(request, "Your friend's encryption keys are invalid. Ask them to log in again.")
        return redirect("chat:dashboard")

    cooldown.clear("chat", curr_user.username, friend.username)

    my_keys = None
    mine = Keys.objects.filter(user=curr_user).first()
    if mine is not None and mine.public_key and mine.signing_key:
        try:
            my_keys = {"enc": json.loads(mine.public_key), "sig": json.loads(mine.signing_key)}
        except json.JSONDecodeError:
            my_keys = None

    return render(request, "chat/messages.html",
                  _base_context(request, curr_user, friend=friend, friend_keys=friend_keys, my_keys=my_keys))


@login_required
@require_safe
def waiting_room(request):
    """Waiting room shown until the friend opens the chat with the current user."""
    curr_user = _profile_or_none(request.user)
    friend = UserProfile.objects.filter(username=request.GET.get("user", "")).first()
    if curr_user is None or friend is None:
        messages.error(request, "That user doesn't exist.")
        return redirect("chat:dashboard")

    mine = Friends.objects.filter(user=curr_user, friend=friend).first()
    theirs = Friends.objects.filter(user=friend, friend=curr_user).first()

    if mine is None or theirs is None:
        messages.error(request, f"You can't chat with {friend.username} until you are friends.")
        return redirect("chat:dashboard")
    if not mine.accepted:
        # They sent us a request we haven't answered yet.
        return redirect(f"/request?user={friend.username}")
    if not theirs.accepted:
        messages.info(request, f"You can chat with {friend.username} once they accept your friend request.")
        return redirect("chat:dashboard")

    wait = cooldown.remaining("chat", curr_user.username, friend.username)
    if wait and friend.online_for_id != curr_user.pk:  # fine if *they* are waiting for us
        messages.warning(request, f"{friend.username} declined your chat request. "
                                  f"You can try again in {cooldown.humanize(wait)}.")
        return redirect("chat:dashboard")

    return render(request, "chat/waiting_room.html", _base_context(request, curr_user, friend=friend))


@login_required
@require_POST
def decline_chat(request):
    """
    The current user declines a friend who is waiting for them in the waiting room.
    The friend is told immediately and has to wait a progressively longer
    cool-down before asking again.
    """
    me = _profile_or_none(request.user)
    other = UserProfile.objects.filter(username=request.POST.get("user", "")).first()
    if me is None or other is None or not are_friends(me, other):
        return JsonResponse({"status": False}, status=404)
    if other.online_for_id != me.pk:
        return JsonResponse({"status": False, "message": "They are no longer waiting."})

    wait = cooldown.record_decline("chat", other.username, me.username)
    UserProfile.objects.filter(pk=other.pk, online_for=me).update(online_for=None)
    push_to_user(other.username, {"type": "chat_declined", "from": me.username,
                                  "retry_in": wait, "retry_text": cooldown.humanize(wait)})
    return JsonResponse({"status": True, "retry_in": wait})


@require_safe
def room(request):
    """Returns whether the friend `user` is online and has opened a chat with us."""
    if not request.user.is_authenticated:
        return JsonResponse({"status": False}, status=401)
    for_user = request.GET.get("user", "")
    me = _profile_or_none(request.user)
    other = UserProfile.objects.filter(username=for_user).first()
    if me is None or other is None or not are_friends(me, other):
        return JsonResponse({"status": False})
    return JsonResponse({"status": other.online == 1 and other.online_for_id == me.pk})


@login_required
@require_http_methods(["GET", "POST"])
def FriendRequest(request):
    """GET shows a pending friend request; POST accepts or rejects it."""
    me = _profile_or_none(request.user)
    if me is None:
        return redirect("registration:logout")

    source = request.POST if request.method == "POST" else request.GET
    other_name = source.get("request_from") or source.get("user")
    other = UserProfile.objects.filter(username=other_name or "").first()
    pending = None
    if other is not None:
        pending = Friends.objects.filter(user=me, friend=other, accepted=False).first()
    if pending is None:
        if other is not None and are_friends(me, other):
            return redirect(f"/waiting-room?user={other.username}")
        messages.error(request, "That friend request doesn't exist anymore.")
        if request.method == "POST":
            return JsonResponse({"status": False}, status=404)
        return redirect("chat:dashboard")

    if request.method == "GET":
        return render(request, "chat/FriendRequest.html",
                      _base_context(request, me, RequestFrom=other.username, note=pending.note))

    action = request.POST.get("action")
    if action == "accept":
        Friends.objects.filter(user=me, friend=other).update(accepted=True)
        Friends.objects.filter(user=other, friend=me).update(accepted=True)
        cooldown.clear("friend", me.username, other.username)
        notify_friends_changed(other.username, "accepted", me.username)
        messages.success(request, f"You and {other.username} are now friends.")
        return JsonResponse({"status": True})
    if action == "reject":
        Friends.objects.filter(user=me, friend=other).delete()
        Friends.objects.filter(user=other, friend=me).delete()
        wait = cooldown.record_decline("friend", other.username, me.username)
        notify_friends_changed(other.username, "rejected", me.username,
                               retry_in=wait, retry_text=cooldown.humanize(wait))
        messages.info(request, f"Friend request from {other.username} rejected.")
        return JsonResponse({"status": True})
    return JsonResponse({"status": False}, status=400)


@login_required
@require_safe
def friends_partial(request):
    """HTML fragment of the sidebar friend list (used to refresh it live)."""
    profile = _profile_or_none(request.user)
    if profile is None:
        return JsonResponse({"status": False}, status=400)
    return render(request, "chat/_friends.html", {"friends": getFriendsList(profile.id)})


@login_required
@require_POST
def deleteFriend(request):
    """Removes a friend (both directions)."""
    me = _profile_or_none(request.user)
    friend = UserProfile.objects.filter(username=request.POST.get("friend", "")).first()
    if me is None or friend is None or not Friends.objects.filter(user=me, friend=friend).exists():
        return JsonResponse({"status": False, "message": "Friend not found."}, status=404)

    Friends.objects.filter(user=me, friend=friend).delete()
    Friends.objects.filter(user=friend, friend=me).delete()
    # Make sure neither side keeps a stale "waiting for" pointer.
    UserProfile.objects.filter(pk=me.pk, online_for=friend).update(online_for=None)
    UserProfile.objects.filter(pk=friend.pk, online_for=me).update(online_for=None)
    notify_friends_changed(friend.username, "removed", me.username)
    return JsonResponse({"status": True, "message": "Friend deleted successfully!"})
