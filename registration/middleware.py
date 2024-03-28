from django.http import HttpResponseForbidden
from PrivatePing.settings import DOMAIN

class AllowDesktopOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.user_agent.is_mobile or request.user_agent.is_tablet:
            allows = ["/", "/home", "/robots.txt", "/humans.txt", "/favicon.ico"]
            if not request.path in allows:
                return HttpResponseForbidden("<h2 style='margin-top:50%; text-align:center;'>Sorry, PrivatePing works only on desktop. Please use a desktop to get the best experience!</h2>")
            else:
                return self.get_response(request)

        response = self.get_response(request)
        return response

class FrameOptionsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["X-Frame-Options"] = "ALLOW-FROM " + DOMAIN
        response["Content-Security-Policy"] = "frame-ancestors " + DOMAIN
        response["X-Content-Security-Policy"] = "frame-ancestors " + DOMAIN
        response["Referrer-Policy"] = "same-origin"
        
        return response