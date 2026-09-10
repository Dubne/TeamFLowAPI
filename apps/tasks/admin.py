from django.contrib import admin
from .models import Task, Tag, Comment, Attachment


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0

class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    readonly_fields = ("filename", "size", "content_type", "uploaded_by", "created_at")

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    filter_horizontal = ("tags",)
    inlines = [CommentInline, AttachmentInline]
    list_display = ["title", "project", "assignee", "status", "priority", "sla_due_at"]
    list_filter = ['status', "priority", "project__team"]
    search_fields = ["title", "description", "project__name"]
    readonly_fields = ("created_at", "updated_at")
