from rest_framework import serializers
from .models import User
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer

class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "avatar"]

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta: 
        model = User
        fields = [
            "id",
            "username",
            "email",
            "avatar",
            "first_name",
            "last_name",
            "date_joined",
        ]
        
class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ["id", "username", "email", "password", "first_name", "last_name"]