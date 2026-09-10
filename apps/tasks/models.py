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
    tags = models.ManyToManyField("Task", blank=True, related_name="tasks")
    sla_due_at = models.DateTimeField(null=True, blank=True) 
    def __str__(self):
        return self.title

class Comment(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = 'PUBLIC', "Public"
        INTERNAL = "INTERNAL", "Internal"
    visibility = models.CharField(max_length=50, choices=Visibility.choices, default=Visibility.PUBLIC)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Tag(models.Model):
    name = models.CharField(max_length=50)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="tags")
    class Meta:
        constraints =[
            models.UniqueConstraint(fields=["team", "name"], name="unique_tag_per_team")
        ] 
    def __str__(self):
        return self.name

class Attachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="attachments")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    file = models.FileField(upload_to="attachments/%Y/%m/")
    filename = models.CharField(max_length=255)
    size = models.PositiveIntegerField()
    content_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


    
