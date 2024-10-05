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
from .views import vacancy_update_algorithm
from celery import current_app


logger = logging.getLogger('subscriptions')


@receiver(pre_save, sender=RoomProfile)
def process_vacancy(sender, instance, **kwargs):
    logger.info(
        f'process_vacancy: {instance.pk}, vacancy: {instance.vacancy}, {instance.is_vacant}')

    if not RoomProfile.objects.filter(pk=instance.pk).exists():
        if instance.is_vacant == False:
            logger.info(
                f'Room profile with id {instance.pk} created and is occupied')
            return

        logger.info(
            f'Room profile with id {instance.pk} created and is vacant')

        clients_email_list = vacancy_update_algorithm(instance)
        if clients_email_list:
            send_vacancy_update_mail.delay(clients_email_list)
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

            subscribed_listings = SubscribedListing.objects.filter(
                subscription_handler__is_expired=False,
                room_profile=instance,
                status=SubscribedListing.Status.UNVERIFIED
            )

            logger.info(f'Subscribed listings {subscribed_listings}')

            for subscribed_listing in subscribed_listings:
                subscribed_listing.status = SubscribedListing.Status.REJECTED

                current_app.control.revoke(
                    subscribed_listing.status_task_id,
                    terminate=True
                )
                subscribed_listing.status_task_id = None
                subscribed_listing.save()
                logger.info(
                    f"Subscribed listing for client {subscribed_listing.subscription.client.email}\n"
                    f"Status updated: UNVERIFIED -> REJECTED\n"
                    "status_task_id set to None."
                )

                subscription_handler = subscribed_listing.subscription_handler
                if subscription_handler.queued_listings_count > 0:
                    subscription_handler.queued_listings_count -= 1
                    subscription_handler.save()

                logger.info(
                    f'Subscribed listing with ID {subscribed_listing.pk} rejected. \n'
                    f'Queued listings for subscription handler with ID {subscription_handler.pk} decremented to {subscription_handler.queued_listings_count}.'
                )
            return

        logger.info(
            f'Room profile with id {instance.pk} updated and is vacant')

        clients_email_list = vacancy_update_algorithm(instance)
        if clients_email_list:
            send_vacancy_update_mail.delay(clients_email_list)
    except RoomProfile.DoesNotExist as e:
        logger.error(f'Room profile update failed with exception: {e}')


@receiver(post_save, sender=SubscribedListing)
def schedule_status_change(sender, instance, created, **kwargs):
    """Called only when subscribed listing is created"""

    logger.info('Begin subscribed lisiting scheduling')
    if created:
        logger.info(
            f'Calling change status to verified function for subscribed listing {instance.pk}')
        result = change_status_to_verified.apply_async(
            args=[instance.id],
            countdown=30  # 600s - 10 minutes
        )

        instance.status_task_id = result.id
        instance.save()
