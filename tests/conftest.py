from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.projects.services import create_project
from apps.tasks.models import Task
from apps.tasks.services import create_task
from apps.teams.models import TeamMembership
from apps.teams.services import create_team

User = get_user_model()


@pytest.fixture(autouse=True)
def _isolated_infrastructure(settings, tmp_path):
    settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    settings.MEDIA_ROOT = tmp_path

    from django.core.cache import cache
    cache.clear() 

    from TeamFlowAPI.celery import app
    app.conf.task_always_eager = True     
    app.conf.task_eager_propagates = True 


@pytest.fixture
def password():
    return "StrongPass12345"


@pytest.fixture
def user_factory(db, password):
    counter = {"n": 0}

    def make(username=None, **extra):
        counter["n"] += 1
        username = username or f"user{counter['n']}"
        return User.objects.create_user(
            username=username, email=f"{username}@test.com", password=password, **extra
        )

    return make


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def client_for():
    def make(user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    return make


@pytest.fixture
def team_ctx(user_factory):
    owner, admin, member, viewer, outsider = (
        user_factory(name) for name in ("owner", "admin", "member", "viewer", "outsider")
    )
    team = create_team(owner=owner, name="Backend", description="Backend team")
    for user, role in (
        (admin, TeamMembership.Role.ADMIN),
        (member, TeamMembership.Role.MEMBER),
        (viewer, TeamMembership.Role.VIEWER),
    ):
        TeamMembership.objects.create(user=user, team=team, role=role)
    project = create_project(creator=owner, name="API", description="", team=team)
    return SimpleNamespace(
        owner=owner, admin=admin, member=member, viewer=viewer,
        outsider=outsider, team=team, project=project,
    )


@pytest.fixture
def task(team_ctx):
    return create_task(
        title="Fix bug", description="details", project=team_ctx.project,
        creator=team_ctx.member, priority=Task.Priority.HIGH,
    )
