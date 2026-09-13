from rest_framework import serializers
from .models import Team, TeamMembership, Invitation
from ..users.serializers import UserShortSerializer
from django.contrib.auth import get_user_model

User = get_user_model()
 
class TeamSerializer(serializers.ModelSerializer):
    owner = UserShortSerializer(read_only=True)
    class Meta:
        model = Team
        fields = ["id", "name", "description", "created_at", "updated_at", "owner"]
        read_only_fields = ["owner", "created_at", "updated_at"]

class TeamShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id", "name"]
        
class TeamCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["name", "description"]

class TeamMembershipSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    class Meta:
        model = TeamMembership
        fields = ["id","user","role","joined_at"]

class TeamMembershipRoleUpdateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=TeamMembership.Role.choices)

class InvitationSerializer(serializers.ModelSerializer):
    invited_by = UserShortSerializer(read_only=True)
    invited_user = UserShortSerializer(read_only=True)
    team = TeamSerializer(read_only=True)
    class Meta:
        model = Invitation
        fields = ["id", "status", "team", "invited_user", "invited_by", "expired_at", "created_at"]
        read_only_fields = fields

class InvitationCreateSerializer(serializers.ModelSerializer):
    invited_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    class Meta:
        model = Invitation
        fields = ["invited_user"]
