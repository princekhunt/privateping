from django.contrib import admin
from django.urls import path, include
from registration import views as rv
from .settings import SECRET_ADMIN_URL
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path(SECRET_ADMIN_URL + 'admin/', admin.site.urls),
    path("", include("registration.urls")),
    path("", include("chat.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)