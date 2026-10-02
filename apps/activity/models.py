from django.db import models
from django.conf import settings

from apps.projects.models import Project
from apps.teams.models import Team
from apps.tasks.models import Task

class ActivityLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    team = models.ForeignKey(Team, blank=True, null=True, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, blank=True, null=True, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, blank=True, null=True, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    metadata = models.JSONField(default=dict, blank=True)
    date = models.DateTimeField(auto_now_add=True)