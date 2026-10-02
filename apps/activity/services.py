from apps.activity.models import ActivityLog

def log_activity(*, actor, action, team=None, project=None, task=None, metadata=None):
    ActivityLog.objects.create(
        actor=actor,
        team=team,
        project=project,
        task=task,
        action=action,
        metadata=metadata or {},
    )