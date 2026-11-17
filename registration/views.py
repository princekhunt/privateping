from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe, require_http_methods

from chat.models import Friends, Keys, UserProfile
from registration import pow as proof_of_work
from registration.forms import SignUpForm, username_validator
from registration.models import facts, user_type
from registration.security import (InvalidKey, check_and_hit, clean_encryption_jwk,
                                   clean_signing_jwk, client_ip, is_rate_limited, reset)
from registration.tools import generate_username

# Brute-force protection for the login form
LOGIN_LIMIT_PER_USER = 5      # failed attempts per username ...
LOGIN_LIMIT_PER_IP = 20       # ... or per IP ...
LOGIN_WINDOW = 15 * 60        # ... within 15 minutes


def _random_fact():
    return facts.objects.order_by('?').first()


@require_safe
def Home(request):
    """Landing page. Logged in users go straight to the dashboard."""
    if request.user.is_authenticated:
        return redirect('chat:dashboard')
    return render(request, "registration/Home.html", {"fact": _random_fact()})


@never_cache
@require_http_methods(["GET", "POST"])
def Login(request):
    """
    Username/password login with per-user and per-IP throttling.
    After logging in the browser generates a fresh E2EE key pair (GenerateKeys).
    """
    if request.user.is_authenticated:
        return redirect('chat:dashboard')

    context = {"fact": _random_fact()}
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        ip = client_ip(request)
        user_key = username.lower()

        if is_rate_limited("login-user", user_key, LOGIN_LIMIT_PER_USER, LOGIN_WINDOW) or \
                is_rate_limited("login-ip", ip, LOGIN_LIMIT_PER_IP, LOGIN_WINDOW):
            context["error"] = "Too many failed attempts. Please wait 15 minutes and try again."
            return render(request, "registration/Login.html", context, status=429)

        user = authenticate(request, username=username, password=password) if username and password else None
        # Anonymous accounts have no usable password, so they can never log in here.
        if user is not None:
            reset("login-user", user_key)
            login(request, user)
            return redirect("registration:generate_keys")

        check_and_hit("login-user", user_key, LOGIN_LIMIT_PER_USER, LOGIN_WINDOW)
        check_and_hit("login-ip", ip, LOGIN_LIMIT_PER_IP, LOGIN_WINDOW)
        context["error"] = "Invalid username or password."
        context["username"] = username
        return render(request, "registration/Login.html", context, status=401)

    return render(request, "registration/Login.html", context)


@never_cache
@require_http_methods(["GET", "POST"])
def GenerateKeys(request):
    """
    GET: page that generates the key pairs in the browser.
    POST: stores the user's *public* encryption and signing keys after strict validation.
    The private keys never leave the browser (they are non-extractable WebCrypto keys).
    """
    if not request.user.is_authenticated:
        if request.method == "POST":
            return JsonResponse({"status": "error", "message": "Not logged in."}, status=401)
        return redirect('registration:login')

    if request.method == "POST":
        user = UserProfile.objects.filter(user=request.user).first()
        if user is None:
            return JsonResponse({"status": "error", "message": "Profile missing."}, status=400)
        try:
            public_key = clean_encryption_jwk(request.POST.get("public_key"))
            signing_key = clean_signing_jwk(request.POST.get("signing_key"))
        except InvalidKey as exc:
            return JsonResponse({"status": "error", "message": f"Invalid key: {exc}"}, status=400)

        Keys.objects.update_or_create(user=user, defaults={"public_key": public_key,
                                                           "signing_key": signing_key})
        # Keep at most one Keys row per user (older versions could create duplicates).
        extra = Keys.objects.filter(user=user).order_by("-id")[1:]
        Keys.objects.filter(pk__in=[k.pk for k in extra]).delete()
        return JsonResponse({"status": "ok", "redirect": "/dashboard"})

    return render(request, "registration/GenerateKeys.html")


def _destroy_anonymous_account(user):
    profile = UserProfile.objects.filter(user=user).first()
    if profile is not None:
        Friends.objects.filter(user=profile).delete()
        Friends.objects.filter(friend=profile).delete()
        profile.delete()
    user_type.objects.filter(user=user).delete()
    user.delete()


@never_cache
@require_http_methods(["GET", "POST"])
def Logout(request):
    """
    POST logs out (GET only shows a confirmation, so other sites can't log users out).
    Public keys are wiped server side; the logged_out page wipes private keys in the browser.
    Anonymous accounts are deleted completely.
    """
    if request.method == "GET":
        if not request.user.is_authenticated:
            return render(request, "registration/LoggedOut.html")
        return render(request, "registration/Logout.html")

    if request.user.is_authenticated:
        user = request.user
        with transaction.atomic():
            profile = UserProfile.objects.filter(user=user).first()
            if profile is not None:
                UserProfile.objects.filter(online_for=profile).update(online_for=None)
                profile.online = 0
                profile.online_for = None
                profile.save(update_fields=["online", "online_for"])
                Keys.objects.filter(user=profile).update(public_key="", signing_key="")

            anonymous = user_type.objects.filter(user=user, type="Anonymous").exists()
            logout(request)
            if anonymous:
                _destroy_anonymous_account(user)

    response = render(request, "registration/LoggedOut.html")
    response.delete_cookie("notified")
    response.delete_cookie("Anotified")
    response.delete_cookie("public_key")
    return response


@never_cache
@require_http_methods(["GET", "POST"])
def Signup(request):
    """Account registration with server-side validation and per-IP throttling."""
    if request.user.is_authenticated:
        return redirect('chat:dashboard')

    context = {"fact": _random_fact()}
    if request.method == "POST":
        if check_and_hit("signup-ip", client_ip(request), limit=10, window=3600):
            context["errors"] = ["Too many sign-ups from your network. Please try again later."]
            return render(request, "registration/Signup.html", context, status=429)

        data = request.POST.copy()
        data["email"] = (data.get("username") or "user") + "@noemailrequired.com"
        form = SignUpForm(data)

        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                UserProfile.objects.create(user=user, name=form.cleaned_data["name"],
                                           username=form.cleaned_data["username"])
                user_type.objects.create(user=user, type="regular")
            messages.success(request, "Account created! Please log in.")
            return redirect("registration:login")

        context["errors"] = [e for errs in form.errors.values() for e in errs]
        context["name"] = data.get("name", "")
        context["username"] = data.get("username", "")
        return render(request, "registration/Signup.html", context, status=400)

    return render(request, "registration/Signup.html", context)


@require_safe
def UsernameCheck(request):
    """AJAX: is a username free / valid? Throttled to make enumeration expensive."""
    if check_and_hit("username-check", client_ip(request), limit=120, window=60):
        return JsonResponse({"status": "error", "message": "Too many requests."}, status=429)

    username = request.GET.get("username", "")
    valid = True
    try:
        username_validator(username)
    except Exception:
        valid = False
    exists = UserProfile.objects.filter(username=username).exists()
    user_self = bool(exists and request.user.is_authenticated and request.user.username == username)
    return JsonResponse({
        "status": "ok",
        "available": not exists and valid and 5 <= len(username) <= 20,
        "valid": valid,
        "exists": exists,
        "self": user_self,
    })


@never_cache
@require_http_methods(["GET", "POST"])
def AnonymousDirectLogin(request):
    """
    Creates a temporary account (deleted on logout or after 24h).
    Bots are kept out by a privacy-friendly proof-of-work check (registration/pow.py)
    plus a honeypot field and per-IP limits - no third-party CAPTCHA.
    """
    if request.user.is_authenticated:
        return redirect('chat:dashboard')

    ip = client_ip(request)
    if request.method == "POST":
        if is_rate_limited("anon-ip", ip, limit=10, window=3600):
            return JsonResponse({"status": "error", "message": "Too many temporary accounts from your network. "
                                                                "Please try again later."}, status=429)
        if request.POST.get("website"):  # honeypot: invisible to people, filled in by naive bots
            return JsonResponse({"status": "error", "message": "Verification failed."}, status=400)
        try:
            proof_of_work.verify(request.POST.get("challenge"), request.POST.get("nonce"))
        except proof_of_work.InvalidSolution as exc:
            expired = str(exc) in ("expired", "already used")
            return JsonResponse({"status": "error", "retry": expired,
                                 "message": "Verification expired - retrying." if expired else "Verification failed."},
                                status=400)
        check_and_hit("anon-ip", ip, limit=10, window=3600)
        proof_of_work.record_success(ip)

        with transaction.atomic():
            username = generate_username()
            user = User(username=username, email=username + "@noemailrequired.com")
            user.set_unusable_password()  # can only ever use this session
            user.save()
            user_type.objects.create(user=user, type="Anonymous")
            UserProfile.objects.create(user=user, name=username, username=username)

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return JsonResponse({"status": "ok", "redirect": "/generate_keys/"})

    return render(request, "registration/AnonymousDirectLogin.html", {"pow": proof_of_work.issue(ip)})


@never_cache
@require_safe
def AnonymousChallenge(request):
    """A fresh proof-of-work challenge (used when the previous one expired)."""
    return JsonResponse(proof_of_work.issue(client_ip(request)))


@require_safe
def Base(request):
    """Outer page that frames the app."""
    return render(request, "registration/iframe_base.html")
