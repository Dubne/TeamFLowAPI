from rest_framework import serializers
from .models import Tag, Task, Attachment, Team, Comment
from ..users.serializers import UserShortSerializer
from ..projects.serializers import ProjectShortSerializer
from ..projects.models import Project
from django.contrib.auth import get_user_model
import os
User = get_user_model() 

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]

class TaskListSerializer(serializers.ModelSerializer):
    assignee = UserShortSerializer(read_only=True)
    project = ProjectShortSerializer(read_only=True)
    class Meta:
        model = Task
        fields = ["id", "title", "status", "priority", "assignee", "project", "sla_due_at"]


class TaskDetailSerializer(serializers.ModelSerializer):
    assignee = UserShortSerializer(read_only=True)
    creator = UserShortSerializer(read_only=True)
    project = ProjectShortSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    class Meta:
        model = Task
        fields = [
            "id", "title", "description", "project", "creator", "assignee",
            "status", "priority", "tags", "sla_due_at", "created_at", "updated_at",
        ]
class TaskCreateSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    class Meta:
        model = Task
        fields = ["title", "description", "project", "priority"]

class TaskUpdatedSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Task
        fields = ["title", "description", "priority"]

class TaskAssignSerializer(serializers.Serializer):
    assignee = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

class TaskChangeStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Task.Status.choices)

class CommentSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = ["id", "user", "text", "created_at", "updated_at"]

class CommentCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["text"]


ALLOWED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".pdf", ".log", ".txt"]
MAX_SIZE_MB = 10


class AttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = UserShortSerializer(read_only=True)

    class Meta:
        model = Attachment
        fields = ["id", "file", "filename", "size", "content_type", "uploaded_by", "created_at"]
        read_only_fields = fields


class AttachmentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ["file"]

    def validate_file(self, value):
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        if value.size > MAX_SIZE_MB * 1024 * 1024:
            raise serializers.ValidationError(f"File is too big (max {MAX_SIZE_MB} MB).")
        return value