from .models import Project
from ..teams.models import TeamMembership
from ..tasks.models import Task
from django.db.models import Count, Q
from django.utils import timezone
def get_user_visible_projects(*, user):
    user_teams = TeamMembership.objects.filter(user=user).values_list("team_id", flat=True)
    return Project.objects.filter(team_id__in=user_teams).select_related("team")

def get_project_statistic(*, project):
    stats = Task.objects.filter(project=project).aggregate(
        total_tasks = Count("id"),
        open_tasks = Count("id", filter=Q(status=Task.Status.OPEN)),
        in_progress_tasks =  Count("id", filter=Q(status=Task.Status.IN_PROGRESS)),
        resolved_tasks =  Count("id", filter=Q(status=Task.Status.RESOLVED)),
        closed_tasks =  Count("id", filter=Q(status=Task.Status.CLOSED)),
        sla_breached = Count("id", filter=Q(sla_due_at__lt=timezone.now()) & ~Q(status=Task.Status.CLOSED) & ~Q(status=Task.Status.RESOLVED)),

    )
    stats["resolution_rate"] = (
        round(stats["resolved_tasks"] / stats["total_tasks"] * 100, 1)
        if stats["total_tasks"] else 0
    )
    return stats