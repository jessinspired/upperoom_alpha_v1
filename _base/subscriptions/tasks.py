#!/usr/bin/env python3
from celery import shared_task
from django.utils import timezone
from .models import SubscribedListing
import logging

logger = logging.getLogger('subscriptions')


@shared_task
def change_status_to_verified(subscribed_listing_id):
    logger.info('In change_status_to_verified -> subscriptions.task')
    try:
        subscribed_listing = SubscribedListing.objects.get(
            id=subscribed_listing_id)

        if subscribed_listing.status == SubscribedListing.Status.UNVERIFIED:
            subscribed_listing.status = SubscribedListing.Status.VERIFIED
            subscribed_listing.save()
            logger.info(
                f'Status changed to verified for subscribed_listing with id {subscribed_listing_id}')
        else:
            logger.info(
                f'Cannot verify listing with status: {subscribed_listing.status}\nlisting pk: {subscribed_listing_id}')
    except SubscribedListing.DoesNotExist:
        logger.error(
            f'subscribed_listing does not exist for id: {subscribed_listing_id}')
