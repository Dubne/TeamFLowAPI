"""Тесты сервисного слоя tasks."""

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.exceptions import Throttled

from apps.activity.models import ActivityLog
from apps.projects.models import Project
from apps.tasks.models import Attachment, Comment, Tag, Task
from apps.tasks.services import (
    add_tag_to_task,
    assign_task,
    change_task_status,
    check_task_creation_rate_limit,
    create_comment,
    create_tag,
    create_task,
    delete_attachment,
    delete_comment,
    delete_tag,
    delete_task,
    remove_tag_from_task,
    update_comment,
    update_task,
    upload_attachment,
)
from apps.teams.models import TeamMembership
from apps.teams.services import create_team

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
            title="t",
            project=team_ctx.project,
            creator=team_ctx.member,
            priority=Task.Priority.LOW,
        )


def test_create_task_requires_writable_team_membership(team_ctx):
    with pytest.raises(ValidationError, match="read-only"):
        create_task(
            title="t",
            project=team_ctx.project,
            creator=team_ctx.viewer,
            priority=Task.Priority.LOW,
        )

    with pytest.raises(ValidationError, match="not a member"):
        create_task(
            title="t",
            project=team_ctx.project,
            creator=team_ctx.outsider,
            priority=Task.Priority.LOW,
        )


def test_create_task_records_activity(team_ctx):
    task = create_task(
        title="New task",
        description="details",
        project=team_ctx.project,
        creator=team_ctx.member,
        priority=Task.Priority.MEDIUM,
    )

    log = ActivityLog.objects.get(task=task, action="task_created")
    assert log.actor == team_ctx.member
    assert log.metadata == {"title": "New task", "priority": Task.Priority.MEDIUM}


def test_assign_rejects_user_from_another_team(team_ctx, task):
    with pytest.raises(ValidationError, match="member of the team"):
        assign_task(task=task, assigner=team_ctx.admin, assignee=team_ctx.outsider)


def test_plain_member_cannot_assign(team_ctx, task):
    with pytest.raises(ValidationError):
        assign_task(task=task, assigner=team_ctx.member, assignee=team_ctx.member)


def test_admin_can_assign_task_and_assignment_is_logged(team_ctx, task):
    assigned = assign_task(task=task, assigner=team_ctx.admin, assignee=team_ctx.member)

    task.refresh_from_db()
    assert assigned == task
    assert task.assignee == team_ctx.member
    log = ActivityLog.objects.get(task=task, action="task_assigned")
    assert log.actor == team_ctx.admin
    assert log.metadata == {"assignee_id": team_ctx.member.id}


def test_member_who_is_not_assignee_cannot_change_status(team_ctx, task):
    with pytest.raises(ValidationError):
        change_task_status(
            task=task, user=team_ctx.member, status=Task.Status.IN_PROGRESS
        )


def test_assignee_can_change_status(team_ctx, task):
    task.assignee = team_ctx.member
    task.save(update_fields=["assignee"])

    updated = change_task_status(
        task=task, user=team_ctx.member, status=Task.Status.IN_PROGRESS
    )

    task.refresh_from_db()
    assert updated.status == Task.Status.IN_PROGRESS
    assert task.status == Task.Status.IN_PROGRESS


def test_status_change_rejects_invalid_status_without_modifying_task(team_ctx, task):
    with pytest.raises(ValidationError, match="Invalid task status"):
        change_task_status(task=task, user=team_ctx.admin, status="NOT_A_STATUS")

    task.refresh_from_db()
    assert task.status == Task.Status.OPEN
    assert not ActivityLog.objects.filter(
        task=task, action="task_status_changed"
    ).exists()


def test_status_change_is_logged_with_old_and_new_value(team_ctx, task):
    change_task_status(task=task, user=team_ctx.admin, status=Task.Status.IN_PROGRESS)

    log = ActivityLog.objects.get(task=task, action="task_status_changed")
    assert log.actor == team_ctx.admin
    assert log.metadata == {"old_status": "OPEN", "new_status": "IN_PROGRESS"}


def test_task_creator_can_delete_task_and_deletion_is_logged(team_ctx, task):
    task_id = task.id

    delete_task(task=task, user=team_ctx.member)

    assert not Task.objects.filter(id=task_id).exists()
    log = ActivityLog.objects.get(action="task_deleted")
    assert log.actor == team_ctx.member
    assert log.task is None
    assert log.metadata == {"deleter_id": team_ctx.member.id}


def test_admin_can_delete_another_members_task(team_ctx, task):
    delete_task(task=task, user=team_ctx.admin)

    assert not Task.objects.filter(id=task.id).exists()


def test_non_creator_member_cannot_delete_task(team_ctx, task, user_factory):
    teammate = user_factory("teammate")
    TeamMembership.objects.create(
        team=team_ctx.team, user=teammate, role=TeamMembership.Role.MEMBER
    )

    with pytest.raises(ValidationError, match="Only the creator or a team admin"):
        delete_task(task=task, user=teammate)


def test_admin_can_update_task_fields_and_priority_resets_sla(team_ctx, task):
    old_deadline = task.sla_due_at

    updated = update_task(
        task=task,
        user=team_ctx.admin,
        title="Updated title",
        description="Updated description",
        priority=Task.Priority.CRITICAL,
    )

    task.refresh_from_db()
    assert updated == task
    assert task.title == "Updated title"
    assert task.description == "Updated description"
    assert task.priority == Task.Priority.CRITICAL
    assert task.sla_due_at != old_deadline
    assert abs((task.sla_due_at - timezone.now()) - timedelta(hours=4)) < timedelta(
        seconds=5
    )


def test_task_update_without_priority_preserves_sla(team_ctx, task):
    old_deadline = task.sla_due_at

    update_task(task=task, user=team_ctx.owner, title="Updated title")

    task.refresh_from_db()
    assert task.title == "Updated title"
    assert task.sla_due_at == old_deadline


@pytest.mark.parametrize("user_attr", ["member", "outsider"])
def test_non_admin_cannot_update_task(team_ctx, task, user_attr):
    with pytest.raises(ValidationError):
        update_task(task=task, user=getattr(team_ctx, user_attr), title="Not allowed")

    task.refresh_from_db()
    assert task.title == "Fix bug"


def test_create_comment_records_preview(team_ctx, task):
    text = "x" * 120

    comment = create_comment(task=task, user=team_ctx.member, text=text)

    assert Comment.objects.get(id=comment.id).text == text
    log = ActivityLog.objects.get(task=task, action="comment_created")
    assert log.actor == team_ctx.member
    assert log.metadata == {"comment_id": comment.id, "text_preview": text[:100]}


def test_cannot_create_comment_as_non_member(team_ctx, task):
    with pytest.raises(ValidationError, match="not a member"):
        create_comment(task=task, user=team_ctx.outsider, text="No access")

    assert not Comment.objects.filter(task=task).exists()


def test_comment_author_can_update_comment(team_ctx, task):
    comment = Comment.objects.create(task=task, user=team_ctx.member, text="Initial")

    updated = update_comment(comment=comment, user=team_ctx.member, text="Updated")

    comment.refresh_from_db()
    assert updated == comment
    assert comment.text == "Updated"


def test_user_cannot_update_another_members_comment(team_ctx, task):
    comment = Comment.objects.create(task=task, user=team_ctx.owner, text="Initial")

    with pytest.raises(ValidationError, match="own comment"):
        update_comment(comment=comment, user=team_ctx.member, text="Changed")

    comment.refresh_from_db()
    assert comment.text == "Initial"


def test_comment_author_and_admin_can_delete_comment(team_ctx, task):
    own_comment = Comment.objects.create(task=task, user=team_ctx.member, text="Own")
    other_comment = Comment.objects.create(
        task=task, user=team_ctx.member, text="Other"
    )

    delete_comment(comment=own_comment, user=team_ctx.member)
    delete_comment(comment=other_comment, user=team_ctx.admin)

    assert not Comment.objects.filter(
        id__in=[own_comment.id, other_comment.id]
    ).exists()


def test_member_cannot_delete_another_members_comment(team_ctx, task):
    comment = Comment.objects.create(task=task, user=team_ctx.owner, text="Other")

    with pytest.raises(ValidationError, match="permission to delete"):
        delete_comment(comment=comment, user=team_ctx.member)

    assert Comment.objects.filter(id=comment.id).exists()


def test_create_tag_and_reject_duplicate(team_ctx):
    tag = create_tag(team=team_ctx.team, creator=team_ctx.member, name="bug")

    assert tag.team == team_ctx.team
    assert tag.name == "bug"
    with pytest.raises(ValidationError, match="already exists"):
        create_tag(team=team_ctx.team, creator=team_ctx.admin, name="bug")

    assert Tag.objects.filter(team=team_ctx.team, name="bug").count() == 1


def test_viewer_cannot_create_tag(team_ctx):
    with pytest.raises(ValidationError, match="read-only"):
        create_tag(team=team_ctx.team, creator=team_ctx.viewer, name="bug")


def test_add_and_remove_tag_from_task(team_ctx, task):
    tag = create_tag(team=team_ctx.team, creator=team_ctx.member, name="bug")

    add_tag_to_task(task=task, tag=tag, user=team_ctx.member)

    assert task.tags.filter(id=tag.id).exists()
    log = ActivityLog.objects.get(task=task, action="tag_to_task_added")
    assert log.actor == team_ctx.member
    assert log.metadata == {"tag_id": tag.id, "tag_name": tag.name}

    remove_tag_from_task(task=task, tag=tag, user=team_ctx.member)

    assert not task.tags.filter(id=tag.id).exists()


def test_cannot_add_tag_from_another_team(team_ctx, task):
    other_team = create_team(owner=team_ctx.owner, name="Other", description="")
    other_tag = create_tag(team=other_team, creator=team_ctx.owner, name="external")

    with pytest.raises(ValidationError, match="different team"):
        add_tag_to_task(task=task, tag=other_tag, user=team_ctx.member)

    assert not task.tags.filter(id=other_tag.id).exists()


def test_only_admin_can_delete_tag(team_ctx):
    tag = create_tag(team=team_ctx.team, creator=team_ctx.member, name="bug")

    with pytest.raises(ValidationError, match="permission to delete tag"):
        delete_tag(tag=tag, team=team_ctx.team, deleter=team_ctx.member)

    delete_tag(tag=tag, team=team_ctx.team, deleter=team_ctx.admin)

    assert not Tag.objects.filter(id=tag.id).exists()


def test_upload_attachment_records_file_metadata(team_ctx, task):
    file = SimpleUploadedFile("note.txt", b"test content", content_type="text/plain")

    attachment = upload_attachment(task=task, file=file, uploaded_by=team_ctx.member)

    assert attachment.task == task
    assert attachment.uploaded_by == team_ctx.member
    assert attachment.filename == "note.txt"
    assert attachment.size == len(b"test content")
    assert attachment.content_type == "text/plain"
    with attachment.file.open("rb") as stored_file:
        assert stored_file.read() == b"test content"


def test_cannot_upload_attachment_as_non_member(team_ctx, task):
    file = SimpleUploadedFile("note.txt", b"content", content_type="text/plain")

    with pytest.raises(ValidationError, match="not a member"):
        upload_attachment(task=task, file=file, uploaded_by=team_ctx.outsider)

    assert not Attachment.objects.filter(task=task).exists()


def test_attachment_uploader_and_admin_can_delete_attachment(team_ctx, task):
    own_attachment = upload_attachment(
        task=task,
        file=SimpleUploadedFile("own.txt", b"own content", content_type="text/plain"),
        uploaded_by=team_ctx.member,
    )
    own_stored_name = own_attachment.file.name
    delete_attachment(attachment=own_attachment, user=team_ctx.member)

    assert not Attachment.objects.filter(id=own_attachment.id).exists()
    assert not own_attachment.file.storage.exists(own_stored_name)

    attachment = upload_attachment(
        task=task,
        file=SimpleUploadedFile(
            "admin.txt", b"admin content", content_type="text/plain"
        ),
        uploaded_by=team_ctx.member,
    )
    stored_name = attachment.file.name

    delete_attachment(attachment=attachment, user=team_ctx.admin)

    assert not Attachment.objects.filter(id=attachment.id).exists()
    assert not attachment.file.storage.exists(stored_name)


def test_member_cannot_delete_another_members_attachment(team_ctx, task):
    attachment = upload_attachment(
        task=task,
        file=SimpleUploadedFile("note.txt", b"content", content_type="text/plain"),
        uploaded_by=team_ctx.owner,
    )
    stored_name = attachment.file.name

    with pytest.raises(ValidationError, match="permission to delete"):
        delete_attachment(attachment=attachment, user=team_ctx.member)

    assert Attachment.objects.filter(id=attachment.id).exists()
    assert attachment.file.storage.exists(stored_name)


def test_task_creation_rate_limit_allows_twenty_then_throttles(team_ctx):
    for _ in range(20):
        check_task_creation_rate_limit(user_id=team_ctx.member.id)

    with pytest.raises(Throttled, match="rate limit"):
        check_task_creation_rate_limit(user_id=team_ctx.member.id)
