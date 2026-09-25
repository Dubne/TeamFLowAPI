from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.permissions import IsTeamMember
from .models import Team 
from .serializers import TeamSerializer, TeamCreateUpdateSerializer, InvitationSerializer, \
      TeamMembershipRoleUpdateSerializer, TeamMembershipSerializer, InvitationCreateSerializer, TransferOwnershipSerializer
from .selectors import get_user_teams, get_team_invitations, get_team_members, get_user_incoming_invitations
from .services import create_team, update_team, delete_team, transfer_team_ownership, \
    remove_member, change_member_role, invite_user, accept_invitation, decline_invitation


class TeamViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsTeamMember()]

    def get_queryset(self):
        return get_user_teams(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return TeamCreateUpdateSerializer
        return TeamSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team = create_team(user=request.user, **serializer.validated_data)
        return Response(TeamSerializer(team).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        team = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_team = update_team(user=request.user, team=team, **serializer.validated_data)
        return Response(TeamSerializer(updated_team).data)

    def destroy(self, request, *args, **kwargs):
        team = self.get_object()
        delete_team(team=team, user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["patch"], url_path="transfer-ownership")
    def transfer_ownership(self, request, pk=None):
        team = self.get_object()
        serializer = TransferOwnershipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_team = update_team(team=team, current_owner=request.user, new_owner=serializer.validated_data["new_owner"])
        return Response(TeamSerializer(updated_team).data)
