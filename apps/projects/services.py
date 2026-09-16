from .models import Project
from ..teams.models import TeamMembership
from django.core.exceptions import ValidationError

def create_project(*, creator, name, description="", team):
     
     membership = TeamMembership.objects.filter(user=creator, team=team).first()

     if membership is None:
          raise ValidationError("You are not a team member.")
     if membership.role not in [
               TeamMembership.Role.OWNER,
               TeamMembership.Role.ADMIN
          ]:
          raise ValidationError("You do not have permission to create project")
     
     return Project.objects.create(
          name=name,
          description = description,
          created_by = creator,
          team = team
          )
     
def change_project_status(*, project, user, status):
    membership = TeamMembership.objects.filter(
        team=project.team,
        user=user,
    ).first()

    if membership is None:
        raise ValidationError(
            "You are not a member of this team."
        )

    if membership.role not in [
        TeamMembership.Role.OWNER, 
        TeamMembership.Role.ADMIN,
    ]:
        raise ValidationError(
            "You do not have permission to change project status."
        )

    if status not in Project.Status.values:
        raise ValidationError("Invalid project status.")

    project.status = status
    project.save(update_fields=["status"])

    return project