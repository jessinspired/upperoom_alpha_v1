#!/usr/bin/env python3
"""signals for subscription models"""
from django.db.models.signals import (
    pre_save,
)
from django.dispatch import receiver
from .models import RoomProfile
import logging
from messaging.tasks import send_vacancy_update_mail

logger = logging.getLogger('subscriptions')


@receiver(pre_save, sender=RoomProfile)
def process_vacancy(sender, instance, **kwargs):
    logger.info(
        f'debugging process vacancy')

    if not instance.pk:
        if instance.is_vacant == False:
            return

        logger.info(
            f'Room profile with id {instance.pk} freshly created and is vacant')
        send_vacancy_update_mail(instance.pk)
        return
    try:
        original_instance = RoomProfile.objects.get(pk=instance.pk)
        if original_instance.is_vacant == instance.is_vacant or instance.is_vacant == False:
            return

        logger.info(
            f'Room profile with id {instance.pk} updated and is vacant')

        send_vacancy_update_mail(instance.pk)
    except RoomProfile.DoesNotExist as e:
        logger.error(f'Room profile update failed with exception: {e}')
