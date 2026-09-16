from datetime import timedelta
from django.utils import timezone
from .models import Task
from ..teams.models import TeamMembership
from django.db import transaction
from django.core.exceptions import ValidationError

SLA_BY_PRIORITY = {
    Task.Priority.LOW: timedelta(days=7),
    Task.Priority.MEDIUM: timedelta(days=3),
    Task.Priority.HIGH: timedelta(days=1),
    Task.Priority.CRITICAL: timedelta(hours=4),
}

def create_task(*, title, description="", project, creator, priority):
    sla_due_at = timezone.now() + SLA_BY_PRIORITY[priority]

    membership = TeamMembership.objects.filter(
    team=project.team,
    user=creator,
    ).first()

    if membership is None:
        raise ValidationError("You are not a member of this team.")

    if membership.role not in [
              TeamMembership.Role.OWNER,
              TeamMembership.Role.ADMIN
         ]:
        raise ValidationError("You do not have permission to create a task")
    
    return Task.objects.create(
        project=project,
        creator=creator,
        title=title,
        priority=priority,
        description=description,
        sla_due_at=sla_due_at
    )

@transaction.atomic
def assign_task(*, task, assigner, assignee):
    assigner_membership = TeamMembership.objects.filter(
        team=task.project.team,
        user=assigner,
    ).first()

    if assigner_membership is None:
        raise ValidationError("You are not a member of this team.")

    if assigner_membership.role not in [
        TeamMembership.Role.OWNER,
        TeamMembership.Role.ADMIN,
    ]:
        raise ValidationError(
            "Only team owners and admins can assign tasks."
        )

    assignee_membership = TeamMembership.objects.filter(
        team=task.project.team,
        user=assignee,
    ).first()

    if assignee_membership is None:
        raise ValidationError(
            "Assignee must be a member of the team."
        )

    task.assignee = assignee
    task.save(update_fields=["assignee"])

    return task

@transaction.atomic
def change_task_status(*, task, user, status):
    membership = TeamMembership.objects.filter(
        team=task.project.team,
        user=user,
    ).first()

    if membership is None:
        raise ValidationError(
            "You are not a member of this team."
        )

    if status not in Task.Status.values:
        raise ValidationError("Invalid task status.")

    task.status = status
    task.save(update_fields=["status"])

    return task