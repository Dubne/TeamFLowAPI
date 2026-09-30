import django_filters
from .models import Task, Tag, Attachment

class TaskFilter(django_filters.FilterSet):
    deadline_before = django_filters.DateTimeFilter(field_name="sla_due_at", lookup_expr="lte")
    deadline_after = django_filters.DateTimeFilter(field_name="sla_due_at", lookup_expr="gte")

    class Meta:
        model = Task
        fields = {
            "status": ["exact"],
            "priority": ["exact"],
            "assignee": ["exact"],
            "project": ["exact"],
        }