from rest_framework.routers import DefaultRouter
from django.contrib import admin
from django.urls import path, include
from apps.teams.views import TeamViewSet, TeamMembershipViewSet, InvitationViewSet
from apps.projects.views import ProjectViewSet
from apps.tasks.views import TaskViewSet, CommentViewSet, AttachmentViewSet, TagViewSet, TaskTagViewSet

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

tag_list = TagViewSet.as_view({"get": "list", "post": "create"})
tag_detail = TagViewSet.as_view({"get": "retrieve", "delete": "destroy"})

task_tag_list = TaskTagViewSet.as_view({"get": "list", "post": "create"})
task_tag_detail = TaskTagViewSet.as_view({"delete": "destroy"})

team_membership_list = TeamMembershipViewSet.as_view({"get": "list"})
team_membership_detail = TeamMembershipViewSet.as_view({"delete": "destroy"})
team_membership_change_role = TeamMembershipViewSet.as_view({"patch": "change_role"})

invitation_team_list = InvitationViewSet.as_view({
    "get": "list",
    "post": "create",
})

invitation_list = InvitationViewSet.as_view({
    "get": "list",
})

invitation_accept = InvitationViewSet.as_view({
    "patch": "accept",
})

invitation_decline = InvitationViewSet.as_view({
    "patch": "decline",
})

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include(router.urls)),
    path("tasks/<int:task_pk>/comments/", comment_list, name="task-comments-list"),
    path("comments/<int:pk>/", comment_detail, name="comment-detail"),
    path("tasks/<int:task_pk>/attachments/", attachment_list, name="task-attachments-list"),
    path("attachments/<int:pk>/", attachment_detail, name="attachment-detail"),
    path("teams/<int:pk>/tags/", tag_list, name="team-tags-list"),
    path("tags/<int:pk>/", tag_detail),
    path("tasks/<int:task_pk>/tags/", task_tag_list),
    path("tasks/<int:task_pk>/tags/<int:pk>/", task_tag_detail),
    path("teams/<int:team_pk>/members/", team_membership_list),
    path("teams/<int:team_pk>/members/<int:pk>/", team_membership_detail),
    path("teams/<int:team_pk>/members/<int:pk>/change-role/"),
    path("teams/<int:team_pk>/invitations/", InvitationViewSet.as_view({"get": "list", "post": "create"})),
    path("invitations/", InvitationViewSet.as_view({"get": "list"})),
    path("invitations/<int:pk>/accept/", InvitationViewSet.as_view({"patch": "accept"})),
    path("invitations/<int:pk>/decline/", InvitationViewSet.as_view({"patch": "decline"}))
] 
