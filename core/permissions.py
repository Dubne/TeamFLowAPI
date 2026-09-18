from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.teams.models import TeamMembership
from apps.projects.models import Project
from apps.tasks.models import Task


class IsTeamMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return TeamMembership.objects.filter(user=request.user, team=obj).exists()

class IsProjectTeamMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return TeamMembership.objects.filter(user=request.user, team=obj.team).exists()

class IsTaskTeamMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return TeamMembership.objects.filter(user=request.user, team=obj.project.team).exists()

class IsCommentTeamMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return TeamMembership.objects.filter(user=request.user, team=obj.task.project.team).exists()

class IsTagTeamMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return TeamMembership.objects.filter(user=request.user, team=obj.team).exists()

class IsAttachmentTeamMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return TeamMembership.objects.filter(user=request.user, team=obj.task.project.team).exists()
    
# def get_team(obj):
#     team = getattr(obj, "team", None)
#     if team is None:
#         return obj
#     return team

# class IsTeamMember(BasePermission):
#     def has_object_permission(self, request, view, obj):
#         team = get_team(obj)
#         return TeamMembership.objects.filter(user=request.user, team=team).exists()

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


