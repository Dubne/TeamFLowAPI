"""
Тесты на изоляцию между командами и на нормальные коды ошибок.

ВАЖНО: на текущем коде проекта эти тесты КРАСНЫЕ — это не ошибка в тестах.
Они описывают поведение, которое должно быть. Цикл: запустить -> увидеть красное ->
понять причину -> починить код -> увидеть зелёное.
"""
import pytest
from django.core.exceptions import ValidationError

from apps.projects.services import update_project

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


def test_viewer_cannot_change_task_status_even_when_assigned(client_for, team_ctx, task):
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
