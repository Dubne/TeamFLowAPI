from rest_framework.routers import DefaultRouter
from django.contrib import admin
from django.urls import path, include
from apps.teams.views import TeamViewSet
from apps.projects.views import ProjectViewSet
from apps.tasks.views import TaskViewSet, CommentViewSet, AttachmentViewSet
router = DefaultRouter()
router.register("teams", TeamViewSet, basename="team" )
router.register("projects", ProjectViewSet, basename="project")
router.register("tasks", TaskViewSet, basename="task")

comment_list = CommentViewSet.as_view({
    "get": "list",
    "post": "create",
})

comment_detail = CommentViewSet.as_view({
    "get": "retrieve",
    "patch": "partial_update",
    "put": "update",
    "delete": "destroy",
})

attachment_list = AttachmentViewSet.as_view({
    "get": "list",
    "post": "create",
})

attachment_detail = AttachmentViewSet.as_view({
    "get": "retrieve",
    "delete": "destroy",
})

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include(router.urls)),
    path("tasks/<int:task_pk>/comments/", comment_list, name="task-comments-list"),
    path("comments/<int:pk>/", comment_detail, name="comment-detail"),
    path("tasks/<int:task_pk>/attachments/", attachment_list, name="task-attachments-list"),
    path("attachments/<int:pk>/", attachment_detail, name="attachment-detail"),
] 
