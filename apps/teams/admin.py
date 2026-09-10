from django.contrib import admin
from .models import Team

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "owner")
    search_fields = ("name", "description", "owner__username")
    readonly_fields = ("created_at", "updated_at")