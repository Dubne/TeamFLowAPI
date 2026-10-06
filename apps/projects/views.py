from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.core.cache import cache

from core.permissions import IsProjectTeamMember
from .models import Project
from .serializers import ProjectSerializer, ProjectCreateUpdateSerializer, ChangeStatusSerializer
from .services import create_project, update_project, delete_project, change_project_status
from .selectors import get_project_statistic, get_user_visible_projects
 
class ProjectViewSet(viewsets.ModelViewSet):
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "name"]
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
        updated_project = update_project(project=project, user=request.user, name = serializer.validated_data["name"], description=serializer.validated_data["description"])
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

        cache_key = f"project:statistics:{project.pk}"
        cached_stats = cache.get(cache_key)
        if cached_stats is not None:
            return Response(cached_stats)

        stats = get_project_statistic(project=project)

        cache.set(cache_key, stats, 60)

        return Response(stats)