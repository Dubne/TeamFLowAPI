from .models import Task, Tag, Comment, Attachment
from ..teams.models import TeamMembership, Team

def get_user_visible_tasks(*, user):
    return Task.objects.filter(project__team__memberships__user=user).select_related("project", "creator", "assignee").prefetch_related("tags")

def get_project_tasks(*, project):
    return Task.objects.filter(project=project).select_related("creator", "assignee").prefetch_related("tags")

def get_task_comments(*, task):
    return Comment.objects.filter(task=task).select_related("user")

def get_task_attachments(*, task):
    return Attachment.objects.filter(task=task).select_related("uploaded_by")

def get_team_tags(*, team):
    return Tag.objects.filter(team=team)