from django.contrib import admin
from .models import UserProfile, Friends, Keys

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'name', 'online', 'online_for')
    search_fields = ('username', 'name')
    list_filter = ('online', 'online_for')
    autocomplete_fields = ['user']

@admin.register(Friends)
class FriendsAdmin(admin.ModelAdmin):
    list_display = ['user', 'friend', 'accepted']
    autocomplete_fields = ['user', 'friend']
    search_fields = ['user__username', 'friend__username']
    list_filter = ['accepted']

@admin.register(Keys)
class KeysAdmin(admin.ModelAdmin):
    list_display = ['user', 'public_key']
    search_fields = ['user__username']
    autocomplete_fields = ['user']


admin.site.site_header = "PrivatePing Admin"
