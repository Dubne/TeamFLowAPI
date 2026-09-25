from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.permissions import IsProjectTeamMember
from .models import Project
from .serializers import ProjectSerializer, ProjectCreateUpdateSerializer, ChangeStatusSerializer
from .services import create_project, update_project, delete_project, change_project_status
from .selectors import get_project_statistic, get_user_visible_projects
 
class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()] 
        return [IsAuthenticated(), IsProjectTeamMember()]

    def get_queryset(self):
        return get_user_visible_projects(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ProjectCreateUpdateSerializer
        return ProjectSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = create_project(creator=request.user, **serializer.validated_data)
        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        project = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_project = update_project(project=project, user=request.user, **serializer.validated_data)
        return Response(ProjectSerializer(updated_project).data)

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        delete_project(project=project, deleter=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["patch"], url_path="change-status")
    def change_status(self, request, pk=None):
        project = self.get_object()
        serializer = ChangeStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_project = change_project_status(project=project, user=request.user, status=serializer.validated_data["status"])
        return Response(ProjectSerializer(updated_project).data)

    @action(detail=True, methods=["get"], url_path="statistic")
    def project_statistic(self, request, pk=None):
        project = self.get_object()
        stats = get_project_statistic(project=project)
        return Response(stats)