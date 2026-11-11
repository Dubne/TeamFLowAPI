from .models import ActivityLog


def get_task_activity(*, task):
    return (
        ActivityLog.objects.filter(task=task).select_related("actor").order_by("-date")
    )
