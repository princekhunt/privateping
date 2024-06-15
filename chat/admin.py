from django.contrib import admin
from .models import UserProfile, Friends, Keys

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'username', 'online', 'online_for')
    search_fields = ('name', 'username')
    list_filter = ('online', 'online_for')
    autocomplete_fields = ('online_for', 'user')

@admin.register(Friends)
class FriendsAdmin(admin.ModelAdmin):
    list_display = ('user', 'friend', 'note', 'accepted')
    search_fields = ('user', 'friend')
    list_filter = ('accepted', )
    autocomplete_fields = ('user', 'friend')

@admin.register(Keys)
class KeysAdmin(admin.ModelAdmin):
    list_display = ('user', 'public_key')
    search_fields = ('user', )
    autocomplete_fields = ('user', )
    


admin.site.site_header = "PrivatePing Admin"