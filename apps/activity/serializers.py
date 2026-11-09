from rest_framework import serializers

from .models import ActivityLog
from ..users.serializers import UserShortSerializer


class ActivityLogSerializer(serializers.Serializer):
    actor = UserShortSerializer(read_only=True)
    class Meta:
        model = ActivityLog
        fields = (
            "id",
            "actor",
            "action",
            "metadata",
            "date",
        )