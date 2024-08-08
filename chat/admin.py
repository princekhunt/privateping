from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group

from .models import UserProfile, Friends, Keys

from unfold.admin import ModelAdmin

admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    pass


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass

@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    list_display = ('username', 'name', 'online', 'online_for')
    search_fields = ('username', 'name')
    list_filter = ('online', 'online_for')
    autocomplete_fields = ['user']

@admin.register(Friends)
class FriendsAdmin(ModelAdmin):
    list_display = ['user', 'friend', 'accepted']
    autocomplete_fields = ['user', 'friend']
    search_fields = ['user__username', 'friend__username']
    list_filter = ['accepted']

@admin.register(Keys)
class KeysAdmin(ModelAdmin):
    list_display = ['user', 'public_key']
    search_fields = ['user__username']
    autocomplete_fields = ['user']


admin.site.site_header = "PrivatePing Admin"
