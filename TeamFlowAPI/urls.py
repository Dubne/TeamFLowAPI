from rest_framework.routers import DefaultRouter
from django.contrib import admin
from django.urls import path, include
from ..apps.teams.views import TeamViewSet
from ..apps.projects.views import ProjectViewSet
from ..apps.tasks.views import TaskViewSet

router = DefaultRouter()
router.register("teams", TeamViewSet, basename="team" )
router.register("projects", ProjectViewSet, basename="project")
router.register("tasks", TaskViewSet, basename="task")

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include(router.urls))
] 
