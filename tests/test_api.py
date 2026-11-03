import pytest
from django.core.cache import cache

from apps.tasks.models import Task
from apps.tasks.services import change_task_status, create_task

pytestmark = pytest.mark.django_db


def test_register_login_and_me(anon_client, password):
    r = anon_client.post(
        "/api/auth/users/",
        {"username": "alex", "email": "alex@test.com", "password": password},
        format="json",
    )
    assert r.status_code == 201, r.data

    r = anon_client.post(
        "/api/auth/jwt/create/", {"username": "alex", "password": password}, format="json"
    )
    assert r.status_code == 200
    anon_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    r = anon_client.get("/api/auth/users/me/")
    assert r.status_code == 200
    assert r.data["username"] == "alex"


def test_task_list_requires_authentication(anon_client):
    assert anon_client.get("/api/tasks/").status_code == 401


def test_member_creates_task(client_for, team_ctx):
    r = client_for(team_ctx.member).post(
        "/api/tasks/",
        {"title": "New", "description": "d", "project": team_ctx.project.id, "priority": "HIGH"},
        format="json",
    )

    assert r.status_code == 201, r.data
    assert r.data["title"] == "New"
    assert r.data["creator"]["username"] == "member"


def test_outsider_does_not_see_foreign_task(client_for, team_ctx, task):
    r = client_for(team_ctx.outsider).get(f"/api/tasks/{task.id}/")

    assert r.status_code == 404  # чужая задача не светится даже как "существующая"


def test_list_is_paginated_and_filterable_by_status(client_for, team_ctx, task):
    in_progress = create_task(
        title="Second", project=team_ctx.project, creator=team_ctx.member,
        priority=Task.Priority.LOW,
    )
    change_task_status(task=in_progress, user=team_ctx.admin, status=Task.Status.IN_PROGRESS)

    r = client_for(team_ctx.member).get("/api/tasks/", {"status": "IN_PROGRESS"})

    assert r.status_code == 200
    assert r.data["count"] == 1
    assert r.data["results"][0]["id"] == in_progress.id


def test_assigning_task_sends_email(client_for, team_ctx, task, mailoutbox):
    r = client_for(team_ctx.admin).patch(
        f"/api/tasks/{task.id}/assign/", {"assignee": team_ctx.member.id}, format="json"
    )

    assert r.status_code == 200, r.data
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == [team_ctx.member.email]


def test_task_creation_is_rate_limited(client_for, team_ctx):
    client = client_for(team_ctx.member)
    payload = {"title": "t", "description": "d", "project": team_ctx.project.id, "priority": "LOW"}

    for _ in range(20):
        assert client.post("/api/tasks/", payload, format="json").status_code == 201

    assert client.post("/api/tasks/", payload, format="json").status_code == 429


def test_project_statistics_are_cached(client_for, team_ctx, task):
    url = f"/api/projects/{team_ctx.project.id}/statistic/"

    r = client_for(team_ctx.member).get(url)

    assert r.status_code == 200
    assert r.data["total_tasks"] == 1
    assert cache.get(f"project:statistics:{team_ctx.project.id}") is not None
