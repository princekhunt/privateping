from django.http import HttpResponseForbidden


class AllowDesktopOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.user_agent.is_mobile or request.user_agent.is_tablet:
            allows = ["/", "/home", "/robots.txt", "/humans.txt", "/favicon.ico"]
            if request.path not in allows:
                return HttpResponseForbidden(
                    "<!doctype html><meta charset='utf-8'><title>PrivatePing</title>"
                    "<h2 style='margin-top:40vh; text-align:center; font-family:sans-serif;'>"
                    "Sorry, PrivatePing works only on desktop. Please use a desktop to get the best experience!</h2>"
                )

        return self.get_response(request)


def build_csp(request):
    """Everything is self-hosted: no third-party scripts, styles, frames or requests at all."""
    host = request.get_host()
    ws = f"wss://{host}" if request.is_secure() else f"ws://{host} wss://{host}"
    return "; ".join([
        "default-src 'self'",
        "script-src 'self'",
        # 'unsafe-inline' is only for style attributes / SweetAlert2's injected
        # <style>; it does not allow script execution.
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data:",
        "font-src 'self' data:",
        "media-src 'self'",
        f"connect-src 'self' {ws}",
        "frame-src 'self'",
        "worker-src 'self'",  # proof-of-work runs in a Web Worker
        "object-src 'none'",
        "base-uri 'none'",
        "form-action 'self'",
        "frame-ancestors 'self'",
    ])


class SecurityHeadersMiddleware:
    """
    Adds a strict Content-Security-Policy (no inline or third-party scripts)
    and other hardening headers to every response.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault("Content-Security-Policy", build_csp(request))
        response.setdefault("Referrer-Policy", "same-origin")
        response.setdefault("Permissions-Policy",
                            "camera=(), microphone=(), geolocation=(), payment=(), usb=(), "
                            "clipboard-write=(self)")
        response.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        response.setdefault("X-Content-Type-Options", "nosniff")
        if request.user.is_authenticated if hasattr(request, "user") else False:
            # Pages with chat UI must never be stored by shared caches.
            response.setdefault("Cache-Control", "no-store")
        return response
