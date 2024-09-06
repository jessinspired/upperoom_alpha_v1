import os

import requests
from core.models import BaseModel
from django.db import models
from django.contrib.auth.models import (
    AbstractUser,
    BaseUserManager,
    Group,
    Permission
)
from django.core.exceptions import ValidationError


class User(BaseModel, AbstractUser):
    """Defines our custom AUTH_USER_MODEL."""
    email = models.EmailField(unique=True)

    class Role(models.TextChoices):
        DEFAULT = 'DEFAULT', 'Default'
        CLIENT = 'CLIENT', 'Client'
        CREATOR = 'CREATOR', 'Creator'

    role = models.CharField(
        max_length=50,
        choices=Role.choices,
        default=Role.DEFAULT
    )

    first_name = models.CharField(max_length=50, null=False)
    last_name = models.CharField(max_length=50, null=False)
    customer_code = models.CharField(max_length=50, default="")

    def save(self, *args, **kwargs):
        """Override save to create a Paystack customer when a user is created."""
        # Check if it's a new user
        if not self.customer_code:
            super().save(*args, **kwargs)  # Save user first to get the ID
            self._create_paystack_customer()
        else:
            super().save(*args, **kwargs)  # Update existing user


    def _create_paystack_customer(self):
        print("Creating customer on paystack...")
        """Create a Paystack customer and save the customer code."""
        url = "https://api.paystack.co/customer"
        headers = {
            "Authorization": f"Bearer {os.getenv('PAYSTACK_TEST_KEY')}",
            "Content-Type": "application/json"
        }
        data = {
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            response_data = response.json()
            self.customer_code = response_data['data']['customer_code']
            print(f"Paystack customer created successfully. Code: {self.customer_code}")
            self.save()
        else:
            response_data = response.json()
            raise ValidationError("Failed to create Paystack customer.")


# Creator models
class CreatorManager(BaseUserManager):
    """Manager for creator proxy table."""

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(role=User.Role.CREATOR)


class Creator(User):
    """Defines the creator proxy model."""

    objects = CreatorManager()

    class Meta:
        proxy = True

    def welcome(self):
        return "Only for creators"

    def save(self, *args, **kwargs):
        """Saves creator object and adds it to the 'creators' group."""
        self.role = User.Role.CREATOR
        super().save(*args, **kwargs)

        creators_group, created = Group.objects.get_or_create(name="creators")

        if not self.groups.filter(name="creators").exists():
            self.groups.add(creators_group)

    def delete(self, *args, **kwargs):
        """Removes creator from group before deleting."""
        self.groups.remove(Group.objects.get(name='creators'))
        super().delete(*args, **kwargs)


class CreatorProfile(BaseModel):
    """Defines attributes and methods for creator profile."""
    user = models.OneToOneField(
        Creator,
        on_delete=models.CASCADE,
        related_name='creator_profile'
    )
    phone_number = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} profile"


# Client models
class ClientManager(BaseUserManager):
    """Manager for client proxy table."""

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(role=User.Role.CLIENT)


class Client(User):
    """Defines the Client proxy model."""

    objects = ClientManager()

    class Meta:
        proxy = True

    def welcome(self):
        return "Only for clients"

    def save(self, *args, **kwargs):
        """Saves client object and adds it to the 'clients' group."""
        self.role = User.Role.CLIENT
        super().save(*args, **kwargs)

        clients_group, created = Group.objects.get_or_create(name="clients")

        if not self.groups.filter(name="clients").exists():
            self.groups.add(clients_group)

    def delete(self, *args, **kwargs):
        """Removes client from group before deleting."""
        self.groups.remove(Group.objects.get(name='clients'))
        super().delete(*args, **kwargs)


class ClientProfile(BaseModel):
    """Defines methods and attributes for Client."""
    user = models.OneToOneField(
        Client,
        on_delete=models.CASCADE,
        related_name='client_profile'
    )
    phone_number = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} profile"
