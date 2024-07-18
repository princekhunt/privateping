from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from .models import UserProfile, Friends
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser
from channels.db import database_sync_to_async
from chat.models import Keys
import base64
import urllib
from registration.models import user_type
from chat.tools import getFriendsList, getUserId
from django.views.decorators.clickjacking import xframe_options_exempt
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist


def index(request):
    """
    Renders the chat index page. If the user is not authenticated, redirects to the registration home page.
    If the user is anonymous, it renders the Base.html template with anonymous set to True.
    Otherwise, it renders the Base.html template with the list of friends.
    """
    if not request.user.is_authenticated:
        return redirect("registration:home")

    username = request.user.username  # Get username of the logged-in user
    id = getUserId(username)  # Get user ID based on the username
    friends = getFriendsList(id)  # Get friends list for the user

    # Check if the user type is anonymous
    if user_type.objects.get(user=request.user).type == "Anonymous":
        return render(request, "chat/Base.html", {'friends': friends, 'anonymous':True})

    return render(request, "chat/Base.html", {'friends': friends})


def addFriend(request, name):
    """
    Adds a friend to the current user's friend list. If the note exceeds 100 characters, an alert is shown.
    If the friend already exists or the user does not exist, it redirects to the dashboard.
    Otherwise, it saves the new friend relationship.
    """
    note = request.GET.get("note", "")
    if len(note) > 100:
        return HttpResponse(
            "<script>alert('Note too long!'); window.location.href='/dashboard';</script>"
        )

    friend = get_object_or_404(UserProfile, username=name)
    current_user = get_object_or_404(UserProfile, username=request.user.username)

    if Friends.objects.filter(user=current_user, friend=friend).exists():
        return redirect("/dashboard")

    # Create a new friend relationship for the user
    Friends.objects.create(user=current_user, friend=friend, accepted=True)

    # Create a new friend relationship for the friend
    Friends.objects.create(user=friend, friend=current_user, note=note, accepted=False)

    return redirect("/dashboard")

@xframe_options_exempt
def chat(request, username):
    """
    Renders the chat page with the specified user. If the user is not found, it redirects to the dashboard.
    It also sets a cookie with the friend's public key.
    """
    try:
        friend = UserProfile.objects.get(username=username)  # Get the friend's UserProfile
    except UserProfile.DoesNotExist:
        return redirect("chat:dashboard")
    id = getUserId(request.user.username)  # Get the current user's ID
    curr_user = UserProfile.objects.get(id=id)  # Get the current user's UserProfile

    #messages = Messages.objects.filter(sender_name=id, receiver_name=friend.id) | Messages.objects.filter(sender_name=friend.id, receiver_name=id)
    public_key = Keys.objects.get(user=friend).public_key  # Get the friend's public key
    public_key = base64.b64encode(public_key.encode('utf-8')).decode('utf-8')# encode the public key
    public_key = urllib.parse.quote_plus(public_key)  # URL encode the public key
    friends = getFriendsList(id)  # Get the friends list for the current user

    # Check if the user type is anonymous
    if user_type.objects.get(user=request.user).type == "Anonymous":
        response = render(request, "chat/messages.html",
                        {
                         'curr_user': curr_user, 'friends': friends, 'friend':friend, 'anonymous':True})
        response.set_cookie('public_key', public_key)  # Set the public key in a cookie
        return response


    if request.method == "GET":
        response = render(request, "chat/messages.html",
                      {
                       'friends': friends,
                       'curr_user': curr_user, 'friend': friend})
        response.set_cookie('public_key', public_key)  # Set the public key in a cookie
        return response

@xframe_options_exempt
def waiting_room(request):
    """
    Renders the waiting room page where users can wait for their friends to join the chat.
    If the user is not authenticated, it redirects to the home page.
    It checks if the friend request is accepted before allowing the user to chat.
    """
    if not request.user.is_authenticated:
        return redirect('/')
    try:

        if request.method == 'GET':
            user = request.GET.get('user')  # Get the username of the friend from the request
            curr_user = UserProfile.objects.get(username=request.user.username)  # Get the current user's UserProfile
            friend = UserProfile.objects.get(username=user)  # Get the friend's UserProfile

            # Check if the friend request is not accepted
            if Friends.objects.filter(user=curr_user.id, friend=friend).exists():
                if Friends.objects.get(user=curr_user.id, friend=friend).accepted == False:
                    #redirect with get parameter
                    return redirect(f"/request?user={user}")

            # Check if the friend request is not accepted by the friend
            if Friends.objects.filter(user=friend, friend=curr_user.id).exists():
                if Friends.objects.get(user=friend, friend=curr_user.id).accepted == False:
                    return HttpResponse("<script>alert('You cannot chat with this user until, they accept your friend request!'); window.location.href='/';</script>")

            # Check if the friend relationship does not exist
            if not Friends.objects.filter(user=curr_user.id, friend=friend).exists() or not Friends.objects.filter(user=friend, friend=curr_user.id).exists():
                return HttpResponse("<script>alert('You cannot chat with this user until, they add you as a friend!'); window.location.href='/';</script>")

        username = request.user.username  # Get the username of the current user
        id = getUserId(username)  # Get the current user's ID
        friends = getFriendsList(id)  # Get the friends list for the current user

        return render(request, "chat/waiting_room.html", {"friend": friend.name, 'friends': friends})
    except:
        return HttpResponse("<script>alert('something went wrong'); window.location.href='/';</script>")
    
@xframe_options_exempt
def room(request):
    """
    Checks if the specified user is online and available for chat.
    Returns a JSON response indicating the online status.
    """
    if request.method == "GET":
        ForUser = request.GET.get("user")  # Get the username of the friend from the request
        try:
            # Check if the friend is online and available for chat
            if UserProfile.objects.get(username=str(ForUser)).online==1 and UserProfile.objects.get(username=str(ForUser)).online_for==UserProfile.objects.get(username=request.user.username):
                return JsonResponse({"status": True})
            else:
                return JsonResponse({"status": False})
        except Exception as e:
            pass
        return JsonResponse({"status": False})
    return JsonResponse({"status": False})

def FriendRequest(request):
    """
    Handles the friend request process. If the request method is GET, it renders the friend request page.
    If the request method is POST, it accepts or rejects the friend request based on the user's action.
    """
    if not request.user.is_authenticated:
        return redirect('registration:login')
    
    if request.method == "GET":
        if not request.GET.get("user"):
            return redirect("chat:dashboard")
    
        friend = request.GET.get("user")  # Get the username of the friend from the request
        try:
            # Check if the friend request exists
            if Friends.objects.filter(user=UserProfile.objects.get(user=request.user), friend=UserProfile.objects.get(user=User.objects.get(username=friend))).exists():
                note = Friends.objects.get(user=UserProfile.objects.get(user=request.user), friend=UserProfile.objects.get(user=User.objects.get(username=friend))).note

                username = request.user.username  # Get the username of the current user
                id = getUserId(username)  # Get the current user's ID
                friends = getFriendsList(id)  # Get the friends list for the current user

                return render(request, "chat/FriendRequest.html", {"RequestFrom": friend, "note": note, 'friends': friends})
        except ObjectDoesNotExist:
            return redirect("chat:dashboard")
        
    if request.method == "POST":
        request_from = request.POST.get("request_from")  # Get the username of the friend from the request
        #validations
        if Friends.objects.filter(user=UserProfile.objects.get(user=request.user), friend=UserProfile.objects.get(user=User.objects.get(username=request_from))).exists():
            action = request.POST.get("action")  # Get the action (accept/reject) from the request
            if action == "accept":
                friend = UserProfile.objects.get(user=User.objects.get(username=request_from))  # Get the friend's UserProfile
                Friends.objects.filter(user=UserProfile.objects.get(user=request.user), friend=friend).update(accepted=True) # Accept the friend request
                Friends.objects.filter(user=friend, friend=UserProfile.objects.get(user=request.user)).update(accepted=True)  # Update the friend request status
                return redirect("chat:dashboard")
            elif action == "reject":
                friend = UserProfile.objects.get(user=User.objects.get(username=request_from))  # Get the friend's UserProfile
                Friends.objects.filter(user=UserProfile.objects.get(user=request.user), friend=friend).delete()  # Delete the friend request
                Friends.objects.filter(user=friend, friend=UserProfile.objects.get(user=request.user)).delete()  # Delete the friend request from the friend's side
                return redirect("chat:dashboard")

    return render(request, "chat/FriendRequest.html")

def deleteFriend(request):
    """
    Deletes a friend from the current user's friend list.
    If the user is not authenticated, it redirects to the login page.
    If the friend exists, it deletes the friend relationship.
    """
    if not request.user.is_authenticated:
        return redirect("registration:login")
    
    if request.method == "GET":
        friend = request.GET.get("friend")  # Get the username of the friend from the request
        try:
            # Check if the friend relationship exists
            if Friends.objects.filter(user=UserProfile.objects.get(user=request.user), friend=UserProfile.objects.get(user=User.objects.get(username=friend))).exists():
                friend = UserProfile.objects.get(user=User.objects.get(username=friend))  # Get the friend's UserProfile
                Friends.objects.filter(user=UserProfile.objects.get(user=request.user), friend=friend).delete()  # Delete the friend relationship
                Friends.objects.filter(user=friend, friend=UserProfile.objects.get(user=request.user)).delete()  # Delete the friend relationship from the friend's side
                return JsonResponse({"status": True, "message": "Friend deleted successfully!"})
        except ObjectDoesNotExist:
            return redirect("chat:dashboard")
    return redirect("chat:dashboard")
