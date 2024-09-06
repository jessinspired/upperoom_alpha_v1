#!/usr/bin/env python3
"""signals for subscription models"""
from django.db.models.signals import (
    pre_save, post_save
)
from django.dispatch import receiver
from .models import RoomProfile
import logging
from messaging.tasks import send_vacancy_update_mail
from .models import Subscription, SubscribedListing
from .tasks import change_status_to_verified

logger = logging.getLogger('subscriptions')


@receiver(pre_save, sender=RoomProfile)
def process_vacancy(sender, instance, **kwargs):
    logger.info(f'process_vacancy: {instance.pk}')

    if not RoomProfile.objects.filter(pk=instance.pk).exists():
        if instance.is_vacant == False:
            logger.info(
                f'Room profile with id {instance.pk} created and is occupied')
            return

        logger.info(
            f'Room profile with id {instance.pk} created and is vacant')
        send_vacancy_update_mail(instance.pk)
        return
    try:
        original_instance = RoomProfile.objects.get(pk=instance.pk)
        if original_instance.is_vacant == instance.is_vacant:
            return

        if instance.is_vacant == False:
            subscriptions = Subscription.objects.filter(
                subscribed_rooms=instance,
                is_expired=False
            )

            for subscription in subscriptions:
                subscription.subscribed_rooms.remove(instance)

            SubscribedListing.objects.filter(
                subscription__is_expired=False,
                room_profile=instance
            ).update(status=SubscribedListing.Status.REJECTED)

            logger.info(
                'room profile removed from subscriptions and substriction lisitng set to rejected')
            return

        logger.info(
            f'Room profile with id {instance.pk} updated and is vacant')

        send_vacancy_update_mail(instance.pk)
    except RoomProfile.DoesNotExist as e:
        logger.error(f'Room profile update failed with exception: {e}')


@receiver(post_save, sender=SubscribedListing)
def schedule_status_change(sender, instance, created, **kwargs):
    logger.info('Begin subscribed lisiting scheduling')
    if created:
        logger.info(
            f'Calling change status to verified function for subscribed listing {instance.pk}')
        change_status_to_verified.apply_async(
            args=[instance.id],
            countdown=120  # 600s - 10 minutes
        )
