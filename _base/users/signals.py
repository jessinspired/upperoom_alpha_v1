#!/usr/bin/env python3
"""signals for user queries"""

from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction

from users.models import (
    Client,
    ClientProfile,
    Creator,
    CreatorProfile,
)


@receiver(post_save, sender=Client)
def create_client_profile(sender, instance, created, **kwargs):
    '''creates client profile when customer user is saved'''
    if created and instance.role == 'CLIENT':
        with transaction.atomic():
            ClientProfile.objects.create(user=instance)
            instance.save()


@receiver(post_save, sender=Creator)
def create_creator_profile(sender, instance, created, **kwargs):
    '''creates creator profile when business is saved'''
    if created and instance.role == 'CREATOR':
        with transaction.atomic():
            CreatorProfile.objects.create(user=instance)
            instance.save()
