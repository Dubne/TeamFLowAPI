from django.contrib import admin
from models import Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "team", "created_by")
    list_filter = ("team", "status")
    search_fields = ("name", "description")
    readonly_fields = ("updated_at", "created_at")  

