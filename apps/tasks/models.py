from django.db import models
from django.conf import settings
from apps.projects.models import Project 
from apps.teams.models import Team
class Task(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", 'open'
        IN_PROGRESS = "IN_PROGRESS", 'In_progress'
        WAITING_ON_CUSTOMER = "WAITING_ON_CUSTOMER", "Waiting_on_customer"
        RESOLVED = "RESOLVED", 'Resolved'
        CLOSED = "CLOSED", 'Closed'
    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"
    title = models.CharField(max_length=50)
    description = models.TextField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_tasks")
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tasks")
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=50, choices=Priority.choices, default=Priority.LOW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sla_due_at = models.DateTimeField(null=True, blank=True)


    
