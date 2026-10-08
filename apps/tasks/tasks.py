from celery import shared_task
from django.utils import timezone

from .models import Task
from apps.activity.services import log_activity
from apps.notifications.tasks import notify_sla_breach


@shared_task
def check_sla_breaches():
    overdue_tasks = (
        Task.objects.filter(sla_due_at__lt=timezone.now(), is_sla_breached=False)
        .exclude(status__in=[Task.Status.RESOLVED, Task.Status.CLOSED])
        .select_related("project__team", "assignee")
    )

    for task in overdue_tasks:
        task.is_sla_breached = True
        task.save(update_fields=["is_sla_breached"])

        log_activity(
            actor=None,
            action="sla_breached",
            team=task.project.team,
            project=task.project,
            task=task,
            metadata={"sla_due_at": task.sla_due_at.isoformat()},
        )

        if task.assignee:
            notify_sla_breach.delay(task.assignee.id, task.title)