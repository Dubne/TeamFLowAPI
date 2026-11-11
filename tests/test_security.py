"""
Тесты на изоляцию между командами и на нормальные коды ошибок.

ВАЖНО: на текущем коде проекта эти тесты КРАСНЫЕ — это не ошибка в тестах.
Они описывают поведение, которое должно быть. Цикл: запустить -> увидеть красное ->
понять причину -> починить код -> увидеть зелёное.
"""

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import Throttled

from apps.projects.services import update_project
from apps.tasks.models import Attachment, Comment
from apps.teams.models import Invitation
from apps.teams.services import create_team, invite_user

pytestmark = pytest.mark.django_db


def test_outsider_cannot_list_task_comments(client_for, team_ctx, task):
    r = client_for(team_ctx.outsider).get(f"/api/tasks/{task.id}/comments/")
    assert r.status_code in (403, 404)


def test_outsider_cannot_list_task_attachments(client_for, team_ctx, task):
    r = client_for(team_ctx.outsider).get(f"/api/tasks/{task.id}/attachments/")
    assert r.status_code in (403, 404)


def test_outsider_cannot_list_team_tags(client_for, team_ctx):
    r = client_for(team_ctx.outsider).get(f"/api/teams/{team_ctx.team.id}/tags/")
    assert r.status_code in (403, 404)


def test_outsider_cannot_list_team_invitations(client_for, team_ctx):
    r = client_for(team_ctx.outsider).get(f"/api/teams/{team_ctx.team.id}/invitations/")
    assert r.status_code in (403, 404)


def test_business_rule_violation_returns_4xx_not_500(client_for, team_ctx, task):
    r = client_for(team_ctx.member).patch(
        f"/api/tasks/{task.id}/assign/", {"assignee": team_ctx.member.id}, format="json"
    )
    assert r.status_code in (400, 403)


def test_viewer_can_read_tasks_and_project_statistics(client_for, team_ctx, task):
    client = client_for(team_ctx.viewer)

    task_list = client.get("/api/tasks/")
    statistics = client.get(f"/api/projects/{team_ctx.project.id}/statistic/")

    assert task_list.status_code == 200
    assert task_list.data["count"] == 1
    assert statistics.status_code == 200
    assert statistics.data["total_tasks"] == 1


def test_viewer_cannot_create_task(client_for, team_ctx):
    response = client_for(team_ctx.viewer).post(
        "/api/tasks/",
        {
            "title": "New",
            "description": "d",
            "project": team_ctx.project.id,
            "priority": "HIGH",
        },
        format="json",
    )

    assert response.status_code == 400


def test_viewer_cannot_change_task_status_even_when_assigned(
    client_for, team_ctx, task
):
    task.assignee = team_ctx.viewer
    task.save(update_fields=["assignee"])

    response = client_for(team_ctx.viewer).patch(
        f"/api/tasks/{task.id}/change-status/",
        {"status": "IN_PROGRESS"},
        format="json",
    )

    assert response.status_code == 403


def test_viewer_cannot_update_project_even_if_they_created_it(team_ctx):
    project = team_ctx.project
    project.created_by = team_ctx.viewer
    project.save(update_fields=["created_by"])

    with pytest.raises(ValidationError, match="read-only"):
        update_project(project=project, user=team_ctx.viewer, name="Changed")

    project.refresh_from_db()
    assert project.name == "API"


def test_team_update_accepts_name_field(client_for, team_ctx):
    response = client_for(team_ctx.owner).patch(
        f"/api/teams/{team_ctx.team.id}/",
        {"name": "Renamed"},
        format="json",
    )

    assert response.status_code == 200, response.data
    team_ctx.team.refresh_from_db()
    assert team_ctx.team.name == "Renamed"


def test_project_update_rejects_team_change(client_for, team_ctx):
    another_team = create_team(owner=team_ctx.owner, name="Another", description="")
    response = client_for(team_ctx.owner).patch(
        f"/api/projects/{team_ctx.project.id}/",
        {"team": another_team.id},
        format="json",
    )

    assert response.status_code == 400
    team_ctx.project.refresh_from_db()
    assert team_ctx.project.team == team_ctx.team


def test_commenting_on_unassigned_task_succeeds(client_for, team_ctx, task):
    response = client_for(team_ctx.member).post(
        f"/api/tasks/{task.id}/comments/",
        {"text": "No assignee yet"},
        format="json",
    )

    assert response.status_code == 201, response.data
    assert Comment.objects.filter(task=task, text="No assignee yet").exists()


def test_comment_detail_route_supports_read_update_and_delete(
    client_for, team_ctx, task
):
    comment = Comment.objects.create(
        task=task,
        user=team_ctx.member,
        text="Initial comment",
    )
    client = client_for(team_ctx.member)

    detail_url = f"/api/comments/{comment.id}/"
    assert client.get(detail_url).status_code == 200
    assert (
        client.patch(detail_url, {"text": "Updated"}, format="json").status_code == 200
    )
    assert client.delete(detail_url).status_code == 204


def test_attachment_detail_route_supports_read_and_delete(client_for, team_ctx, task):
    attachment = Attachment.objects.create(
        task=task,
        uploaded_by=team_ctx.member,
        file=SimpleUploadedFile("note.txt", b"test content"),
        filename="note.txt",
        size=12,
        content_type="text/plain",
    )
    client = client_for(team_ctx.member)

    detail_url = f"/api/attachments/{attachment.id}/"
    assert client.get(detail_url).status_code == 200
    assert client.delete(detail_url).status_code == 204


def test_task_activity_returns_all_activity_fields(client_for, team_ctx, task):
    response = client_for(team_ctx.member).get(f"/api/tasks/{task.id}/activity/")

    assert response.status_code == 200
    entry = next(
        item for item in response.data["results"] if item["action"] == "task_created"
    )
    assert {"id", "actor", "action", "metadata", "date"} <= entry.keys()


def test_invitation_rate_limit_does_not_create_over_limit_invitation(
    team_ctx, user_factory
):
    for index in range(20):
        invited_user = user_factory(f"invitee{index}")
        invite_user(
            inviter=team_ctx.owner,
            invited_user=invited_user,
            team=team_ctx.team,
        )

    over_limit_user = user_factory("invitee-over-limit")
    with pytest.raises(Throttled):
        invite_user(
            inviter=team_ctx.owner,
            invited_user=over_limit_user,
            team=team_ctx.team,
        )

    assert not Invitation.objects.filter(
        team=team_ctx.team,
        invited_user=over_limit_user,
    ).exists()
