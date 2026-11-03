
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.activity.models import ActivityLog
from apps.teams.models import Invitation, TeamMembership
from apps.teams.services import (
    accept_invitation,
    create_team,
    invite_user,
    transfer_team_ownership,
)

pytestmark = pytest.mark.django_db


def test_create_team_makes_creator_owner(user_factory):
    user = user_factory()

    team = create_team(owner=user, name="Alpha", description="")

    assert TeamMembership.objects.get(team=team, user=user).role == TeamMembership.Role.OWNER
    assert ActivityLog.objects.filter(team=team, action="team_created").exists()


def test_plain_member_cannot_invite(team_ctx, user_factory):
    newcomer = user_factory("newcomer")

    with pytest.raises(ValidationError, match="permission"):
        invite_user(inviter=team_ctx.member, invited_user=newcomer, team=team_ctx.team)


def test_admin_can_invite_and_invitation_lives_7_days(team_ctx, user_factory):
    newcomer = user_factory("newcomer")

    invitation = invite_user(inviter=team_ctx.admin, invited_user=newcomer, team=team_ctx.team)

    assert invitation.status == Invitation.Status.PENDING
    lifetime = invitation.expired_at - timezone.now()
    assert timedelta(days=6, hours=23) < lifetime <= timedelta(days=7)


def test_accept_invitation_creates_membership(team_ctx, user_factory):
    newcomer = user_factory("newcomer")
    invitation = invite_user(inviter=team_ctx.owner, invited_user=newcomer, team=team_ctx.team)

    membership = accept_invitation(invitation=invitation, user=newcomer)

    invitation.refresh_from_db()
    assert invitation.status == Invitation.Status.ACCEPTED
    assert membership.role == TeamMembership.Role.MEMBER
    assert TeamMembership.objects.filter(team=team_ctx.team, user=newcomer).exists()


def test_cannot_accept_someone_elses_invitation(team_ctx, user_factory):
    newcomer = user_factory("newcomer")
    invitation = invite_user(inviter=team_ctx.owner, invited_user=newcomer, team=team_ctx.team)

    with pytest.raises(ValidationError):
        accept_invitation(invitation=invitation, user=team_ctx.outsider)


def test_transfer_ownership_swaps_roles(team_ctx):
    transfer_team_ownership(
        team=team_ctx.team, current_owner=team_ctx.owner, new_owner=team_ctx.admin
    )

    team_ctx.team.refresh_from_db()
    roles = dict(
        TeamMembership.objects.filter(team=team_ctx.team).values_list("user__username", "role")
    )
    assert roles["admin"] == "OWNER"
    assert roles["owner"] == "ADMIN"
    assert team_ctx.team.owner == team_ctx.admin
