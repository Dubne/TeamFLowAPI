from rest_framework import serializers
from .models import Project
from ..teams.models import Team
from ..teams.serializers import TeamSerializer, TeamShortSerializer
from ..users.serializers import UserShortSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class ProjectSerializer(serializers.ModelSerializer):
    team = TeamShortSerializer(read_only=True)
    created_by = UserShortSerializer(read_only=True)
    class Meta:
        model = Project
        fields = ["id", "name", "description", "status", "team", "created_by", "created_at", "updated_at"]
        read_only_fields = ["team", "created_by", "created_at", "updated_at"]

class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    class Meta:
        model = Project
        fields = ["name", "description", "team", "status"]

class ProjectShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name"]
    

