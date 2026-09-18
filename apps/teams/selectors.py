from .models import Team, TeamMembership, Invitation

def get_team_members(*, team):
    return TeamMembership.objects.filter(team=team)

def get_user_teams(*, user):
    return Team.objects.filter(memberships__user=user)

def get_user_incoming_invitations(*, user):
    return Invitation.objects.filter(invited_user=user, status=Invitation.Status.PENDING)

def get_team_invitations(*, team):
    return Invitation.objects.filter(team=team)