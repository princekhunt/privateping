from django.contrib import admin

from unfold.admin import ModelAdmin

from .models import facts

@admin.register(facts)
class factsAdmin(ModelAdmin):
    list_display = ('fact',)
    search_fields = ('fact',)
    