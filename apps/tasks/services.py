from datetime import timedelta
from django.utils import timezone
from .models import Task, Comment, Tag, Attachment
from ..teams.models import TeamMembership
from ..projects.models import Project
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

    if project.status == Project.Status.ARCHIVED:
        raise ValidationError("You cannot create a task because this project archived")
    
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

    is_assignee = task.assignee_id == user.id
    is_admin = membership.role in [TeamMembership.Role.OWNER, TeamMembership.Role.ADMIN]
    if not (is_assignee or is_admin):
        raise ValidationError("Only the assignee or a team admin can change the status.")

    if status not in Task.Status.values:
        raise ValidationError("Invalid task status.")

    task.status = status
    task.save(update_fields=["status"])

    return task

def create_comment(*, task, user, text):
    membership = TeamMembership.objects.filter(user=user,team = task.project.team).first()
    if membership is None:
        raise ValidationError("You are not a member of this team")
    return Comment.objects.create(
        task=task,
        user=user,
        text=text,
    )
def update_comment(*, comment, user, text):
    if comment.user != user:
        raise ValidationError("You can only edit your own comment.")
    comment.text = text
    comment.save(update_fields=["text"])
    return comment

def delete_comment(*, comment, user):
    if comment.user == user:
        comment.delete()
        return

    membership = TeamMembership.objects.filter(
        team=comment.task.project.team, user=user
    ).first()
    if membership is None or membership.role not in [
        TeamMembership.Role.OWNER, TeamMembership.Role.ADMIN
    ]:
        raise ValidationError("You do not have permission to delete this comment.")
    comment.delete()

def create_tag(*, team, creator, name):
    membership = TeamMembership.objects.filter(user=creator, team=team).first()
    if membership is None:
        raise ValidationError("You are not a member of this team.")

    if Tag.objects.filter(team=team, name=name).exists():
        raise ValidationError("This tag already exists in the team.")

    return Tag.objects.create(team=team, name=name)


def add_tag_to_task(*, task, tag, user):
    membership = TeamMembership.objects.filter(
        team=task.project.team, user=user
    ).first()
    if membership is None:
        raise ValidationError("You are not a member of this team.")

    if tag.team_id != task.project.team_id:
        raise ValidationError("This tag belongs to a different team.")

    task.tags.add(tag)
    return task


def remove_tag_from_task(*, task, tag, user):
    membership = TeamMembership.objects.filter(
        team=task.project.team, user=user
    ).first()
    if membership is None:
        raise ValidationError("You are not a member of this team.")

    task.tags.remove(tag)
    return task

def upload_attachment(*, task, file, uploaded_by):
    membership = TeamMembership.objects.filter(
        team=task.project.team, user=uploaded_by
    ).first()
    if membership is None:
        raise ValidationError("You are not a member of this team.")

    from .models import Attachment
    return Attachment.objects.create(
        task=task,
        uploaded_by=uploaded_by,
        file=file,
        filename=file.name,
        size=file.size,
        content_type=file.content_type,
    )


def delete_attachment(*, attachment, user):
    if attachment.uploaded_by == user:
        attachment.file.delete(save=False)
        attachment.delete()
        return

    membership = TeamMembership.objects.filter(
        team=attachment.task.project.team, user=user
    ).first()
    if membership is None or membership.role not in [
        TeamMembership.Role.OWNER,
        TeamMembership.Role.ADMIN,
    ]:
        raise ValidationError("You do not have permission to delete this attachment.")

    attachment.file.delete(save=False)
    attachment.delete()