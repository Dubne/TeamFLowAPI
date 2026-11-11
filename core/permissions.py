from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.teams.models import TeamMembership


class IsTeamMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return _has_team_access(request, obj)


class IsProjectTeamMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return _has_team_access(request, obj.team)


class IsTaskTeamMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return _has_team_access(request, obj.project.team)


class IsCommentTeamMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return _has_team_access(request, obj.task.project.team)


class IsTagTeamMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return _has_team_access(request, obj.team)


class IsAttachmentTeamMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return _has_team_access(request, obj.task.project.team)


def _has_team_access(request, team):
    membership = (
        TeamMembership.objects.filter(
            user=request.user,
            team=team,
        )
        .only("role")
        .first()
    )
    if membership is None:
        return False
    return (
        request.method in SAFE_METHODS or membership.role != TeamMembership.Role.VIEWER
    )


# def get_team(obj):
#     team = getattr(obj, "team", None)
#     if team is None:
#         return obj
#     return team

# class IsTeamOwner(BasePermission):
#     def has_object_permission(self, request, view, obj):
#         return TeamMembership.objects.filter(user=request.user, team=obj, role="OWNER").exists()

# class IsTeamAdmin(BasePermission):
#     def has_object_permission(self, request, view, obj):
#         return TeamMembership.objects.filter(user=request.user, team=obj, role__in=["OWNER", "ADMIN"]).exists()

# class IsProjectMember(IsTeamMember):
#     pass

# class IsTaskCreator(BasePermission):
#     def has_object_permission(self, request, view, obj):
#         return obj.creator == request.user

# class IsTaskAssignee(BasePermission):
#     def has_object_permission(self, request, view, obj):
#         return obj.assignee == request.user
