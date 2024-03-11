from django.contrib import admin
from .models import *

admin.site.register(UserProfile)
admin.site.register(Friends)
admin.site.register(Keys)


admin.site.site_header = "PrivatePing Admin"