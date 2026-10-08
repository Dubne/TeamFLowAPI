from celery import shared_task
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from apps.teams.models import Team
User = get_user_model()

@shared_task
def send_task_assigned_notification(assignee_id, task_title):
    try:
        assignee = User.objects.get(id=assignee_id)
    except User.DoesNotExist:
        return
    send_mail(
        subject="You have been assigned a task",
        message=f"The task assigned to you is {task_title}",
        from_email="noreply@teamflow.local",
        recipient_list=[assignee.email],
    )

@shared_task
def send_comment_notification(user_id, comment_text):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return
    send_mail(
        subject="Your task has been commented",
        message=f"Comment text {comment_text}",
        from_email="noreply@teamflow.local",
        recipient_list=[user.email],
    )

@shared_task
def send_invitation_notification(invited_user_id, team_id):
    try:
        user = User.objects.get(id=invited_user_id)
        team = Team.objects.get(id=team_id)
    except (User.DoesNotExist, Team.DoesNotExist):
        return
    send_mail(
        subject= "You have been invited to the team",
        message=f"The team {team.name}",
        from_email="noreply@teamflow.local",
        recipient_list=[user.email],
    )

@shared_task
def notify_sla_breach(assignee_id, task_title):
    try:
        user = User.objects.get(id=assignee_id)
    except User.DoesNotExist:
        return
    send_mail(
        subject="SLA breached",
        message=f"The task '{task_title}' is overdue",
        from_email="noreply@teamflow.local",
        recipient_list=[user.email],
    )