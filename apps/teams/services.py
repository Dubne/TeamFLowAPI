from .models import Team, TeamMembership, Invitation
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError

@transaction.atomic
def create_team(*, owner, name, description=""):
    team = Team.objects.create(
        owner=owner,
        name=name,
        description=description
    )
    TeamMembership.objects.create(
        user=owner,
        team=team,
        role=TeamMembership.Role.OWNER
    ) 
    return team

def invite_user(*, inviter, invited_user, team):
    expired_at = timezone.now() + timedelta(days=7)
    inviter_membership = TeamMembership.objects.filter(user=inviter, team= team).first()

    if inviter_membership is None:
            raise ValidationError("Inviter is not a member of this team")

    if inviter_membership.role not in [
                  TeamMembership.Role.OWNER,
                  TeamMembership.Role.ADMIN
             ]:
            raise ValidationError("You do not have permission to invite a user")
    
    membership = TeamMembership.objects.filter(user=invited_user, team= team).first()
    if membership is not None:
            raise ValidationError("User is already a member of this team")
    
    return Invitation.objects.create(invited_by = inviter, invited_user = invited_user, team=team, expired_at=expired_at)

@transaction.atomic 
def accept_invitation(*, invitation, user):

    if invitation.invited_user != user:
        raise ValidationError("You cannot accept this invitation")
    
    if invitation.status != Invitation.Status.PENDING:
        raise ValidationError()
    
    if invitation.expired_at < timezone.now():
        invitation.status = Invitation.Status.EXPIRED
        invitation.save(update_fields=["status"])
        raise ValidationError("This invitation has expired.")

    if TeamMembership.objects.filter(
        team=invitation.team,
        user=user
    ).exists() :
        raise ValidationError("You are already in this team")
    
    membership = TeamMembership.objects.create(
        user=user,
        team = invitation.team,
        role = TeamMembership.Role.MEMBER
    )

    invitation.status = Invitation.Status.ACCEPTED
    invitation.save(update_fields=["status"])
    
    return membership

@transaction.atomic
def decline_invitation(*, invitation, user):

    if invitation.invited_user != user:
            raise ValidationError("You cannot decline this invitation")
        
    if invitation.status != Invitation.Status.PENDING:
            raise ValidationError()

    if invitation.expired_at < timezone.now():
                invitation.status = Invitation.Status.EXPIRED
                invitation.save(update_fields=["status"])
                raise ValidationError("This invitation has expired.")
    
    invitation.status = Invitation.Status.DECLINED
    invitation.save(update_fields=["status"])

    return invitation

def remove_member(*, remover, member, team):
     
     membership = TeamMembership.objects.filter(
          user=member,
          team = team
     ).first()
     if membership is None:
            raise ValidationError("User is not a member of this team")
     if membership.role == TeamMembership.Role.OWNER:
            raise ValidationError("Team owner cannot be removed") 

     requester_membership = TeamMembership.objects.filter(
          user=remover,
          team=team
     ).first()
     if requester_membership is None:
            raise ValidationError("User is not a member of this team")
     if requester_membership.role not in [
          TeamMembership.Role.OWNER,
          TeamMembership.Role.ADMIN
     ]:
          raise ValidationError("You do not have permission to remove members")
     
     membership.delete()
     return membership
     
def change_member_role(*, member, changer, team, role):
     membership = TeamMembership.objects.filter(
               user=member,
               team = team
          ).first()
     
     if membership is None:
            raise ValidationError("User is not a member of this team")
     if membership.role == TeamMembership.Role.OWNER:
            raise ValidationError("Team owner's role cannot be changed") 
     
     changer_membership = TeamMembership.objects.filter(
               user=changer,
               team = team
          ).first()
     
     if changer_membership is None:
            raise ValidationError("You are not a member of this team")
     if changer_membership.role != TeamMembership.Role.OWNER:
            raise ValidationError("You do not have permission to change member's roles")
     
     if role == TeamMembership.Role.OWNER:
        raise ValidationError(
            "The owner role cannot be assigned this way."
        )
     
     membership.role = role
     membership.save(update_fields=["role"])
     return membership
           
@transaction.atomic
def transfer_team_ownership(*, team, current_owner, new_owner):
    current_membership = TeamMembership.objects.filter(
        team=team,
        user=current_owner,
    ).first()

    if current_membership is None:
        raise ValidationError("You are not a member of this team.")

    if current_membership.role != TeamMembership.Role.OWNER:
        raise ValidationError("Only the team owner can transfer ownership.")

    new_owner_membership = TeamMembership.objects.filter(
        team=team,
        user=new_owner,
    ).first()

    if new_owner_membership is None:
        raise ValidationError(
            "New owner must be a member of the team."
        )

    current_membership.role = TeamMembership.Role.ADMIN
    current_membership.save(update_fields=["role"])

    new_owner_membership.role = TeamMembership.Role.OWNER
    new_owner_membership.save(update_fields=["role"])

    team.owner = new_owner
    team.save(update_fields=["owner"])

    return team