from django.db import models
from django.contrib.auth import get_user_model
from apps.teams.models import Team
from django.conf import settings

class Project(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", 'Active'
        ARCHIVED = "ARCHIVED", 'Archived'
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
