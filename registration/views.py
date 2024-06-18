from django.shortcuts import render, redirect
from registration.forms import SignUpForm, CustomSignupForm
from django.contrib.auth import login, authenticate, logout
from chat.models import UserProfile, Keys, Friends
from django.http import JsonResponse, HttpResponse
from registration.models import facts, user_type
from registration.tools import generate_username
from django.contrib.auth.models import User
from PrivatePing.settings import DOMAIN
import random
# csrf
from django.views.decorators.csrf import csrf_exempt

domain = DOMAIN


def Home(request):
    """
    The Home function handles the initial landing page logic.
    It includes several key steps:

    1. Checks if the user is authenticated; if yes, redirects to the chat dashboard.
    2. Fetches a random fact from the database to display on the home page.
    3. Renders the home page with the fetched fact for GET requests.

    """
    if request.user.is_authenticated:
        return redirect('chat:dashboard')

    fact = facts.objects.order_by('?').first()
    # facts are rendered below the 'Do you know? from the Home.html'
    return render(request, "registration/Home.html", {"fact": fact})


# Skip the csrf verification
@csrf_exempt
def Login(request):
    """
    The Login function handles the process of user authentication and login.
    It includes several key steps:

    1. Checks if the user is already authenticated; if yes, redirects to the chat dashboard.
    2. Fetches a random fact from the database to display on the login page.
    3. Handles POST requests for form submissions and constructs variations of the host URL 
       (with "https://" and "http://") to handle requests without the protocol specified.
    4. Validates the request host and redirects to an error page if it's invalid.
    5. Authenticates the user by fetching the username and password from the request.
    6. Logs the user in if the credentials are valid and redirects to the key generation page.
    7. Renders the login page with an error message if the credentials are invalid.
    8. Renders the login page with a random fact for GET requests.

    """
    if request.user.is_authenticated:
        return redirect('chat:dashboard')

    fact = facts.objects.order_by('?').first()
    if request.method == "POST":
        curr_host = request.META.get("HTTP_HOST")
        if not curr_host.startswith("http"):
            curr_host1 = "https://" + curr_host
            curr_host2 = "http://" + curr_host
        if curr_host1 != domain and curr_host2 != domain:
            return HttpResponse("<script>alert('Invalid Request!'); window.location.href='/login';</script>")
        '''
        Authenticates after fetching the username and the password and logs the user in
        Else in case of invalid credentials login page is rendered with the error
        '''
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
    """
    The GenerateKeys function handles the process of generating and updating keys for end-to-end encryption.
    It includes several key steps:
    
    1. Check whether the user is authenticated or not.
    2. If authenticated, retrieve the user profile and fetch the E2EE key.
    3. Update the key if it already exists; otherwise, store it in the database.
    4. After POST processing, redirect to Dashboard by constructing the absolute URL.
    """
    if not request.user.is_authenticated:
        return redirect('registration:login')
    if request.method == "POST":
        user = UserProfile.objects.get(user=request.user)
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
    """
    The Logout function handles the process of logging out a user from the system.
    It includes several key steps:

    1. Checks if the user is authenticated; if not, redirects to the login page.
    2. If authenticated, retrieve the user's profile and update their status to offline.
    3. Updates any friends' profiles that reference the current user's profile.
    4. Clears the user's public key if it exists.
    5. If the user is of type 'Anonymous', delete associated friends, user type, 
       user profile, and the user account itself.
    6. Logs out the user, ending their session.
    7. Clears local storage and relevant cookies from the user's browser.
    8. Redirect the user to the home page.
    """

    # Check if the user is authenticated; if not, redirect to the login page
    if not request.user.is_authenticated:
        return redirect('registration:login')

    # Proceed if the user is authenticated
    if request.user.is_authenticated:
        # Retrieve the user's profile
        user_profile = UserProfile.objects.get(user=request.user)
        # Set the user profile's online status to offline (0) and clear the 'online_for' field
        user_profile.online = 0
        user_profile.online_for = None
        # Check if there are any users whose 'online_for' field references the current user's profile
        if UserProfile.objects.filter(online_for=user_profile).exists():
            # Retrieve and update such user profiles to set 'online_for' to None
            friends_profile = UserProfile.objects.filter(online_for=user_profile)
            friends_profile.update(online_for=None)
        # Save the updated user profile to the database
        user_profile.save()

        # Check if the user has any associated public keys
        if Keys.objects.filter(user=user_profile).exists():
            # Retrieve the Keys object, clear the public key, and save the changes
            key = Keys.objects.get(user=user_profile)
            key.public_key = ""
            key.save()

        # Check if the user is of type 'Anonymous'
        if user_type.objects.filter(user=request.user, type="Anonymous").exists():
            # If the user has any friends, delete those Friend objects
            if Friends.objects.filter(user=user_profile).exists():
                friends = Friends.objects.filter(user=user_profile)
                friends.delete()
                Friends.objects.filter(friend=user_profile).delete()
            # Delete the 'Anonymous' user type object
            user_type.objects.get(user=request.user, type="Anonymous").delete()
            # Delete the user's profile and the user account itself
            user_profile.delete()
            request.user.delete()

        # Log the user out, ending their session
        logout(request)

    # Create a response that clears local storage and redirects to the home page
    response = HttpResponse("<script>localStorage.clear();parent.location.href = '/';</script>")
    # Delete cookies related to notifications and public key
    response.delete_cookie("notified")
    response.delete_cookie("Anotified")
    response.delete_cookie("public_key")
    # Return the response to the client
    return response


@csrf_exempt
def Signup(request):
    """
    The Signup function handles user registration for the system.
    It includes several key steps:

    1. Checks if the user is already authenticated; if so, redirects to the dashboard.
    2. Retrieves a random fact to display on the signup page.
    3. Processes the POST request to create a new user:
        a. Verifies the request's host.
        b. Copies and modifies the POST data to include a dummy email address.
        c. Validates the signup form.
        d. If valid, saves the new user and associated profile and user type.
        e. If invalid, returns an error message.
    4. Renders the signup page with a random fact if the request method is not POST.
    """

    # Check if the user is authenticated; if so, redirect to the dashboard
    if request.user.is_authenticated:
        return redirect('chat:dashboard')

    # Retrieve a random fact to display on the signup page
    fact = facts.objects.order_by('?').first()

    # Process the POST request to create a new user
    if request.method == "POST":
        # Get the current host
        curr_host = request.META.get("HTTP_HOST")
        # Ensure the host starts with "http"
        if not curr_host.startswith("http"):
            curr_host1 = "https://" + curr_host
            curr_host2 = "http://" + curr_host
        # Check if the host matches the domain
        if curr_host1 != domain and curr_host2 != domain:
            return HttpResponse("<script>alert('Invalid Request!'); window.location.href='/login';</script>")
        # Copy the POST data and modify the email field
        data = request.POST.copy()
        data["email"] = data["username"] + "@noemailrequired.com"
        email = data["email"]
        request.POST = data
        # Create the signup form with the modified POST data
        form = SignUpForm(request.POST)

        # Validate the form
        if form.is_valid():
            # Get the form data
            name = form.cleaned_data.get('name')
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get("password1")
            # Save the new user
            user = form.save()
            # Create and save the user's profile
            profile = UserProfile(user=user, name=name, username=username)
            profile.save()
            # Create and save the user type
            user_type_obj = user_type(user=user, type="regular")
            user_type_obj.save()
            # Redirect to the login page
            return redirect("registration:login")
        else:
            # If the form is invalid, return an error message
            return HttpResponse(
                "<script>alert('Please enter valid details!'); window.location.href='/signup';</script>")
    # Render the signup page with a random fact if the request method is not POST
    return render(request, "registration/Signup.html", {"fact": fact})


def UsernameCheck(request):
    """
    The UsernameCheck function handles AJAX requests to check if a username is available.
    It includes several key steps:

    1. Processes the GET request to check username availability.
    2. Checks if the username exists in the database.
    3. If the username exists, checks if the current authenticated user is the owner of the username.
    4. Returns a JSON response indicating the availability of the username.
    """

    # Process the GET request to check username availability
    if request.method == "GET":
        username = request.GET.get("username")
        user_self = False

        # Check if the username exists in the database
        if UserProfile.objects.filter(username=username).exists():
            # If the user is authenticated, check if they own the username
            if request.user.is_authenticated:
                if request.user.username == username:
                    user_self = True
            # Return a JSON response indicating the username is taken
            return JsonResponse({
                "status": "ok",
                "available": False,
                "self": user_self
            })
        else:
            # Return a JSON response indicating the username is available
            return JsonResponse({
                "status": "ok",
                "available": True,
                "self": user_self
            })

    # Return a JSON response indicating an error if the request method is not GET
    return JsonResponse({
        "status": "error",
        "available": False
    })


def AnonymousDirectLogin(request):
    """
    The AnonymousDirectLogin function handles anonymous user login for the system.
    It includes several key steps:
    1. Checks if the user is already authenticated; if so, redirects to the dashboard.
    2. Processes the POST request to create an anonymous user:
        a. Generates a random username.
        b. Create a random password.
        c. Creates the anonymous user with a dummy email address.
        d. Saves the user and their profile.
        e. Authenticates and logs in the new anonymous user.
        f. Returns a JSON response with a redirect to the generate keys page.
    3. Renders the anonymous direct login page if the request method is not POST.
    """

    # Check if the user is authenticated; if so, redirect to the dashboard
    if request.user.is_authenticated:
        return redirect('chat:dashboard')

    # Process the POST request to create an anonymous user
    if request.method == "POST":
        form = CustomSignupForm(request.POST)

        if form.is_valid():
            # Get the action from the POST request
            action = request.POST.get("action")
            # If the action is to create a new anonymous user
            if action == "create":
                # Generate a random username
                username = generate_username()
                name = username
                # Create a random password
                password = ''.join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890", k=8))
                # Create a dummy email address
                email = username + "@noemailrequired.com"

                # Create the anonymous user with the generated credentials
                user = User.objects.create_user(username=username, email=email, password=password)
                # Save the user type as Anonymous
                user_type.objects.create(user=user, type="Anonymous")
                # Save the user profile
                UserProfile.objects.create(user=user, name=username, username=username)

                # Authenticate and log in the new anonymous user
                user = authenticate(username=username, password=password)
                login(request, user)

                # Return a JSON response with a redirect to the generate keys page
                return JsonResponse(
                    {
                        "status": "ok",
                        "redirect": request.build_absolute_uri("/generate_keys")
                    }
                )
    else:
        form = CustomSignupForm()

    # Render the anonymous direct login page if the request method is not POST
    return render(request, "registration/AnonymousDirectLogin.html", {"form": form})


def Base(request):
    """
    The Base function renders a base iframe template.
    """

    # Render the base iframe template
    return render(request, "registration/iframe_base.html")
