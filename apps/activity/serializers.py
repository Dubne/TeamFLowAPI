from rest_framework import serializers

from .models import ActivityLog
from ..users.serializers import UserShortSerializer


class ActivityLogSerializer(serializers.ModelSerializer):
    actor = UserShortSerializer(read_only=True, allow_null=True)

    class Meta:
        model = ActivityLog
        fields = [
            "id",
            "actor",
            "action",
            "metadata",
            "date",
        ]