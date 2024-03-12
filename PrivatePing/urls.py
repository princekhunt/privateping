from django.contrib import admin
from django.urls import path, include
from registration import views as rv
from .settings import SECRET_ADMIN_URL
urlpatterns = [
    path(SECRET_ADMIN_URL + 'admin/', admin.site.urls),
    path("", include("registration.urls")),
    path("", include("chat.urls")),
]