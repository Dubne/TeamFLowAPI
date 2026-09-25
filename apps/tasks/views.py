from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.teams.models import TeamMembership
from ..projects.models import Project
from core.permissions import IsTaskTeamMember, IsCommentTeamMember, IsTagTeamMember, IsAttachmentTeamMember
from .models import Task, Comment, Tag, Attachment
from .serializers import TaskAssignSerializer, TaskChangeStatusSerializer, TaskCreateSerializer, \
                                TaskDetailSerializer, TaskListSerializer, TaskUpdatedSerializer, CommentCreateUpdateSerializer, CommentSerializer, \
                                AttachmentSerializer, AttachmentUploadSerializer
                                
from .services import create_task, assign_task, delete_task, change_task_status, update_task, create_comment, update_comment, delete_comment
from .selectors import get_project_tasks, get_user_visible_tasks, get_task_attachments, get_task_comments, get_team_tags

class TaskViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsTaskTeamMember()]
    
    def get_queryset(self):
        return get_user_visible_tasks(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == "list":
            return TaskListSerializer
        if self.action == "retrieve":
            return TaskDetailSerializer
        if self.action in ["partial_update", "update"]:
            return TaskUpdatedSerializer
        if self.action == "create":
            return TaskCreateSerializer
        return TaskDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = create_task(creator=request.user, **serializer.validated_data)
        return Response(TaskDetailSerializer(task).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_task = update_task(task=task, user=request.user, **serializer.validated_data)
        return Response(TaskDetailSerializer(updated_task).data)

    def destroy(self, request, *args, **kwargs):
        task = self.get_object()
        delete_task(user=request.user, task=task)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["patch"], url_path="change-status")
    def change_status(self, request, pk=None):
        task = self.get_object()
        serializer = TaskChangeStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_task = change_task_status(task=task, user=request.user, status=serializer.validated_data["status"])
        return Response(TaskDetailSerializer(updated_task).data)
    
    @action(detail=True, methods=["patch"], url_path="assign")
    def assign_task(self, request, pk=None):
        task = self.get_object()
        serializer = TaskAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_task = assign_task(task=task, assigner=request.user, assignee=serializer.validated_data["assignee"])
        return Response(TaskDetailSerializer(updated_task).data)

    @action(detail=False, methods=["get"], url_path="by-project/(?P<project_id>[^/.]+)")
    def by_project(self, request, project_id=None):
        project = get_object_or_404(Project, pk=project_id)
        self.check_object_permissions(request, project)  # проверка через IsProjectTeamMember вручную
        tasks = get_project_tasks(project=project)
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)

class CommentViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        if "task_pk" in self.kwargs:
            task = get_object_or_404(Task, pk=self.kwargs["task_pk"])
            return get_task_comments(task=task)
        return Comment.objects.all()
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CommentCreateUpdateSerializer
        return CommentSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsCommentTeamMember()]
    
    def check_task_permission(self, request, task):
        if not TeamMembership.objects.filter(user=request.user, team=task.project.team).exists():
            self.permission_denied(request, message="You are not a member of this team.")

    def create(self, request, *args, **kwargs):
        task = get_object_or_404(Task, pk=self.kwargs["task_pk"])
        self.check_task_permission(request, task)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = create_comment(task=task, user=request.user, **serializer.validated_data)
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        comment = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = update_comment(comment=comment, user=request.user, **serializer.validated_data)
        return Response(CommentSerializer(updated).data)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        delete_comment(comment=comment, user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

class AttachmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAttachmentTeamMember]

    def get_queryset(self):
        if "task_pk" in self.kwargs:
            task = get_object_or_404(Task, pk=self.kwargs["task_pk"])
            return get_task_attachments(task=task)
        return Attachment.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return AttachmentUploadSerializer
        return AttachmentSerializer

    def create(self, request, *args, **kwargs):
        task = get_object_or_404(Task, pk=self.kwargs["task_pk"])
        if not TeamMembership.objects.filter(user=request.user, team=task.project.team).exists():
            self.permission_denied(request, message="You are not a member of this team.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachment = upload_attachment(
            task=task, file=serializer.validated_data["file"], uploaded_by=request.user
        )
        return Response(AttachmentSerializer(attachment).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        attachment = self.get_object()
        delete_attachment(attachment=attachment, user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
        