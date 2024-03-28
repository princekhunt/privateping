from django.urls import path
from . import views
from django.views.generic.base import TemplateView

app_name = "registration"

urlpatterns = [
    path("", views.Base, name="base"),
    path("home", views.Home, name="home"),
    path("humans.txt", TemplateView.as_view(template_name="registration/humans.txt", content_type="text/plain")),
    path("robots.txt", TemplateView.as_view(template_name="registration/robots.txt", content_type="text/plain")),
    path("signup/", views.Signup, name="register"),
    path("login/", views.Login, name="login"),
    path("AnonymousDirectLogin", views.AnonymousDirectLogin, name="anonymous_direct_login"),
    path("logout/", views.Logout, name="logout"),
    path("generate_keys/", views.GenerateKeys, name="generate_keys"),
    path("api/check_username/", views.UsernameCheck, name="username_check"),
   
]