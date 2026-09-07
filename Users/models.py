from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    password = models.TextField(max_length=12)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
