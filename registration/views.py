from django.shortcuts import render, redirect
from registration.forms import SignUpForm
from django.contrib.auth import login, authenticate, logout
from chat.models import UserProfile, Keys, Friends
from django.http import JsonResponse, HttpResponse
from registration.models import facts, user_type
import random
from registration.tools import generate_username
from django.contrib.auth.models import User
import time

def Home(request):

    if request.user.is_authenticated:
        return redirect('chat:dashboard')

    fact = facts.objects.order_by('?').first()
    
    return render(request, "registration/Home.html", {"fact": fact})

def Login(request):

    if request.user.is_authenticated:
        return redirect('chat:dashboard')

    fact = facts.objects.order_by('?').first()
    
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("registration:generate_keys")
        else:
            error_message = "Invalid credentials!"
            return render(request, "registration/Login.html", {"error": error_message, "fact": fact})

    return render(request, "registration/Login.html", {"fact": fact})


def GenerateKeys(request):
    if not request.user.is_authenticated:
        return redirect('registration:login')

    if request.method == "POST":
        user = UserProfile.objects.get(email=request.user.email)
        public_key = request.POST.get("public_key")
        if Keys.objects.filter(user=user).exists():
            key = Keys.objects.get(user=user)
            key.public_key = public_key
            key.save()
        else:
            SaveKeys = Keys(user=user, public_key=public_key)
            SaveKeys.save()
        return JsonResponse({"redirect": request.build_absolute_uri("/dashboard")})

    return render(request, "registration/GenerateKeys.html")
         

def Logout(request):
    if not request.user.is_authenticated:
        return redirect('registration:login')
        
    if request.user.is_authenticated:
        user_profile = UserProfile.objects.get(email=request.user.email)
        user_profile.online = 0
        user_profile.online_for = None
        if UserProfile.objects.filter(online_for=user_profile).exists():
            friends_profile = UserProfile.objects.filter(online_for=user_profile)
            friends_profile.update(online_for=None)
        user_profile.save()

        if Keys.objects.filter(user=user_profile).exists():
            key = Keys.objects.get(user=user_profile)
            key.public_key = ""
            key.save()
        
        if user_type.objects.filter(user=request.user, type="Anonymous").exists():
            # Unfriend
            if Friends.objects.filter(user=user_profile).exists():
                friends = Friends.objects.filter(user=user_profile)
                friends.delete()
                Friends.objects.filter(friend=user_profile).delete()
            user_type.objects.get(user=request.user, type="Anonymous").delete()
            user_profile.delete()
            request.user.delete()


        logout(request)

    response = HttpResponse("<script>localStorage.clear();window.location.href = '"+ request.build_absolute_uri("../") +"';</script>")
    response.delete_cookie("notified")
    response.delete_cookie("Anotified")
    response.delete_cookie("public_key")
    return response


def Signup(request):
    if request.user.is_authenticated:
        return redirect('chat:dashboard')
    
    fact = facts.objects.order_by('?').first()

    if request.method == "POST":
        data = request.POST.copy()
        data["email"] = data["username"] + "@noemailrequired.com"
        email = data["email"]
        request.POST = data
        form = SignUpForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data.get('name')
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get("password1")
            user = form.save()
            profile = UserProfile(email=email, name=name, username=username)
            profile.save()
            user_type_obj = user_type(user=user, type="regular")
            user_type_obj.save()
            return redirect("registration:login")
        else:
            return HttpResponse("<script>alert('Please enter valid details!'); window.location.href='/signup';</script>")
    return render(request, "registration/Signup.html", {"fact": fact})



def UsernameCheck(request):
    if request.method == "GET":
        username = request.GET.get("username")
        user_self = False
        
        if UserProfile.objects.filter(username=username).exists():
            if request.user.is_authenticated:
                if request.user.username == username:
                    user_self = True
            return JsonResponse({
                "status": "ok",
                "available": False,
                "self": user_self
            })
        else:
            return JsonResponse({
                "status": "ok",
                "available": True,
                "self": user_self
            })

    return JsonResponse({
        "status": "error",
        "available": False
    })

def AnonymousDirectLogin(request):

    if request.user.is_authenticated:
        return redirect('chat:dashboard')

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            username = generate_username()
            name = username
            password = ''.join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890", k=8))
            email = username + "@noemailrequired.com"

            user = User.objects.create_user(username=username, email=email, password=password)
            user_type.objects.create(user=user, type="Anonymous")
            UserProfile.objects.create(email=email, name=username, username=username)

            user = authenticate(username=username, password=password)
            login(request, user)

            return JsonResponse(
                {
                    "status": "ok",
                    "redirect": request.build_absolute_uri("/generate_keys")
                }
            )
    return render(request, "registration/AnonymousDirectLogin.html")