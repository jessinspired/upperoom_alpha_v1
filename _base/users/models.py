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


class CreatorManager(BaseUserManager):
    '''manager for creator proxy table
    Args:
        BaseUserManager (BaseUserManager): Client manager
    '''

    def get_queryset(self, *args, **kwargs):
        '''helps query data belonging to users with role creator
        Returns:
            Creator: creator objects from user table
        '''
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=User.Role.CREATOR)


class Creator(User):
    '''Defines the creator proxy model
    Args:
        User (User): Custom AUTH_USER_MODEL
    Returns:
        Creator: created user(creator) object
    '''
    base_role = User.Role.CREATOR

    objects = CreatorManager()

    class Meta:
        proxy = True

    def welcome(self):
        return "only for creators"

    def save(self, *args, **kwargs):
        '''saves creator object and adds it to group; creators
        '''
        super().save(*args, **kwargs)

        creators_group, created = Group.objects.get_or_create(name="creators")

        # add group permissions here

        self.groups.add(creators_group)

    def delete(self, *args, **kwargs):
        '''removes creator object from group before calling parent delete method
        This is done to prevent a foreign key constraint with the groups table
        '''
        self.groups.remove(Group.objects.get(name='creators'))
        super().delete(*args, **kwargs)


class CreatorProfile(BaseModel):
    '''defines attributes and methods for creator profile
    '''
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    phone_number = models.CharField(
        max_length=50,
        null=True,
        blank=False
    )

    # add more client profile data

    def __str__(self):
        return f"{self.user.username} profile"


# for clients
class ClientManager(BaseUserManager):
    '''manager for client proxy table
    Args:
        BaseUserManager (BaseUserManager): Client manager
    '''

    def get_queryset(self, *args, **kwargs):
        '''helps query data belonging to users with role Client
        Returns:
            Client: client objects from user table
        '''
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=User.Role.CLIENT)


class Client(User):
    '''Defines the Client proxy model
    Args:
        User (User): Custom AUTH_USER_MODEL
    Returns:
        Client: created user(client) object
    '''

    class Meta:
        proxy = True

    def welcome(self):
        return "only for clients"

    def save(self, *args, **kwargs):
        '''saves client object and adds it to group; clients
        '''
        super().save(*args, **kwargs)

        clients_group, created = Group.objects.get_or_create(name="clients")

        # add group permissions here

        self.groups.add(clients_group)

    def delete(self, *args, **kwargs):
        '''removes client object from group before calling parent delete method
        This is done to prevent a foreign key constraint with the groups table
        '''
        self.groups.remove(Group.objects.get(name='clients'))
        super().delete(*args, **kwargs)


class ClientProfile(BaseModel):
    '''defines methods and attributes for Client
    '''
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(
        max_length=50,
        null=True,
        blank=False
    )

    # add more client profile data

    def __str__(self):
        return f"{self.user.username} profile"
