"""
Тесты на изоляцию между командами и на нормальные коды ошибок.

ВАЖНО: на текущем коде проекта эти тесты КРАСНЫЕ — это не ошибка в тестах.
Они описывают поведение, которое должно быть. Цикл: запустить -> увидеть красное ->
понять причину -> починить код -> увидеть зелёное.
"""
import pytest

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
    # обычный member пытается назначать задачи — сервис поднимает ValidationError
    r = client_for(team_ctx.member).patch(
        f"/api/tasks/{task.id}/assign/", {"assignee": team_ctx.member.id}, format="json"
    )
    assert r.status_code in (400, 403)
