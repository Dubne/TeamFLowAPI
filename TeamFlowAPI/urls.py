from rest_framework.routers import DefaultRouter
from django.contrib import admin
from django.urls import path, include
from ..apps.teams.views import TeamViewSet

router = DefaultRouter()
router.register("teams", TeamViewSet, basename="team" )

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include(router.urls))
] 
