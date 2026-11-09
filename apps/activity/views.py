from rest_framework import generics
from .models import ActivityLog
from .serializers import ActivityLogSerializer
from .selectors import get_task_activity
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from ..teams.models import TeamMembership
from ..tasks.models import Task

class TaskActivityView(generics.ListAPIView):
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        task = get_object_or_404(Task.objects.select_related("project__team") ,pk=self.kwargs["task_id"])
        team = task.project.team
        is_member = TeamMembership.objects.filter(team=team, user=self.request.user).exists()
        if is_member:
            return get_task_activity(task=task)
        else:
            raise PermissionDenied("You are not a member of this team.")

