from django.shortcuts import render, HttpResponse, redirect
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

def index(request):
    if not request.user.is_authenticated:
        return redirect("registration:home")

    username = request.user.username
    id = getUserId(username)
    friends = getFriendsList(id)
    if user_type.objects.get(user=request.user).type == "Anonymous":
        return render(request, "chat/Base.html", {'friends': friends, 'anonymous':True})

    return render(request, "chat/Base.html", {'friends': friends})


def addFriend(request, name):
    friend = name
    friend = UserProfile.objects.get(username=name)

    if not UserProfile.objects.filter(username=friend).exists():
        return redirect("/dashboard")

    if Friends.objects.filter(user=UserProfile.objects.get(username=request.user.username), friend=friend).exists():
        return redirect("/dashboard")

    Addfriend = Friends(user=UserProfile.objects.get(username=request.user.username), friend=friend)
    Addfriend.save()

    return redirect("/dashboard")


def chat(request, username):
    try:
        friend = UserProfile.objects.get(username=username)
    except UserProfile.DoesNotExist:
        return redirect("chat:dashboard")
    id = getUserId(request.user.username)
    curr_user = UserProfile.objects.get(id=id)

    #messages = Messages.objects.filter(sender_name=id, receiver_name=friend.id) | Messages.objects.filter(sender_name=friend.id, receiver_name=id)
    public_key = Keys.objects.get(user=friend).public_key
    #base64 encoded
    public_key = base64.b64encode(public_key.encode('utf-8')).decode('utf-8')
    public_key = urllib.parse.quote_plus(public_key)
    friends = getFriendsList(id)
    if user_type.objects.get(user=request.user).type == "Anonymous":
        
        response = render(request, "chat/messages.html",
                        {
                         'curr_user': curr_user, 'friends': friends, 'friend':friend, 'anonymous':True})
        response.set_cookie('public_key', public_key, secure=True)
        return response
    if request.method == "GET":
        response = render(request, "chat/messages.html",
                      {
                       'friends': friends,
                       'curr_user': curr_user, 'friend': friend})
        response.set_cookie('public_key', public_key)
        return response

def waiting_room(request):

    if not request.user.is_authenticated:
        return redirect('/')
    
    try:

        if request.method == 'GET':
            user = request.GET.get('user')
            curr_user = UserProfile.objects.get(username=request.user.username)
            friend = UserProfile.objects.get(username=user)

            if not Friends.objects.filter(user=curr_user.id, friend=friend).exists() or not Friends.objects.filter(user=friend, friend=curr_user.id).exists():
                return HttpResponse("<script>alert('You cannot chat with this user until, they add you as a friend!'); window.location.href='/';</script>")

        username = request.user.username
        id = getUserId(username)
        friends = getFriendsList(id)

        return render(request, "chat/waiting_room.html", {"friend": friend.name, 'friends': friends})
    except:
        return HttpResponse("<script>alert('something went wrong'); window.location.href='/';</script>")

def room(request):
    if request.method == "GET":
        ForUser = request.GET.get("user")
        try:
            if UserProfile.objects.get(username=str(ForUser)).online==1 and UserProfile.objects.get(username=str(ForUser)).online_for==UserProfile.objects.get(username=request.user.username):
                return JsonResponse({"status": True})
            else:
                return JsonResponse({"status": False})
        except Exception as e:
            pass
        return JsonResponse({"status": False})
    return JsonResponse({"status": False})