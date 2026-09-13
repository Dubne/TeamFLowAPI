from rest_framework import serializers
from .models import User

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