from core.models import BaseModel

from django.db import models
from django.contrib.auth.models import (
    AbstractUser,
    BaseUserManager,
    Group,
    Permission
)


class User(BaseModel, AbstractUser):
    '''defines our custom AUTH_USER_MODEL
    (see settings.py; line 137)
    Args:
        AbstractUser (AbstractUser): custom User parent
    '''
    email = models.EmailField(unique=True)

    class Role(models.TextChoices):
        '''defines roles for users
        Args:
            models (TextChoices): Defines the role choices for users
        '''
        DEFAULT = 'DEFAULT', 'Default'
        CLIENT = 'CLIENT', 'Client'
        CREATOR = 'CREATOR', 'Creator'


    # Role.choices here constrains user to only select one of these
    # listed choices.
    role = models.CharField(
        max_length=50,
        choices=Role.choices,
        default=Role.DEFAULT
    )

    first_name = models.CharField(
        max_length=50,
        null=False
    )

    last_name = models.CharField(
        max_length=50,
        null=False
    )
