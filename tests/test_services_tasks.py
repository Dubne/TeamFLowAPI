"""Тесты сервисного слоя tasks."""
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.activity.models import ActivityLog
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.tasks.services import assign_task, change_task_status, create_task

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "priority, expected",
    [
        (Task.Priority.LOW, timedelta(days=7)),
        (Task.Priority.MEDIUM, timedelta(days=3)),
        (Task.Priority.HIGH, timedelta(days=1)),
        (Task.Priority.CRITICAL, timedelta(hours=4)),
    ],
)
def test_sla_deadline_depends_on_priority(team_ctx, priority, expected):
    task = create_task(
        title="t", project=team_ctx.project, creator=team_ctx.member, priority=priority
    )

    actual = task.sla_due_at - timezone.now()
    assert abs(actual - expected) < timedelta(seconds=5)


def test_cannot_create_task_in_archived_project(team_ctx):
    team_ctx.project.status = Project.Status.ARCHIVED
    team_ctx.project.save()

    with pytest.raises(ValidationError, match="archived"):
        create_task(
            title="t", project=team_ctx.project, creator=team_ctx.member,
            priority=Task.Priority.LOW,
        )


def test_assign_rejects_user_from_another_team(team_ctx, task):
    with pytest.raises(ValidationError, match="member of the team"):
        assign_task(task=task, assigner=team_ctx.admin, assignee=team_ctx.outsider)


def test_plain_member_cannot_assign(team_ctx, task):
    with pytest.raises(ValidationError):
        assign_task(task=task, assigner=team_ctx.member, assignee=team_ctx.member)


def test_member_who_is_not_assignee_cannot_change_status(team_ctx, task):
    with pytest.raises(ValidationError):
        change_task_status(task=task, user=team_ctx.member, status=Task.Status.IN_PROGRESS)


def test_status_change_is_logged_with_old_and_new_value(team_ctx, task):
    change_task_status(task=task, user=team_ctx.admin, status=Task.Status.IN_PROGRESS)

    log = ActivityLog.objects.get(task=task, action="task_status_changed")
    assert log.actor == team_ctx.admin
    assert log.metadata == {"old_status": "OPEN", "new_status": "IN_PROGRESS"}
