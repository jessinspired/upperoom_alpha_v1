#!/usr/bin/env python3
from celery import shared_task
from django.utils import timezone
from .models import SubscribedListing, SubscriptionHandler
import logging

logger = logging.getLogger('subscriptions')


@shared_task
def change_status_to_verified(subscribed_listing_id):
    """
    Changes subscribed listing status to verified if
    i. Status is set to unverified

    Credits creator account
    """
    logger.info('In change_status_to_verified -> subscriptions.task')
    try:
        subscribed_listing = SubscribedListing.objects.get(
            id=subscribed_listing_id)

        if subscribed_listing.status == SubscribedListing.Status.UNVERIFIED:
            subscribed_listing.status = SubscribedListing.Status.VERIFIED
            subscribed_listing.creator.transfer_profile.increment_balance()
            subscribed_listing.save()

            # Expiration logic
            # 1. Expire subscription_handler lifecycle (create a method for this)
            subscription_handler = subscribed_listing.subscription_handler

            logger.info(f'subscription handler: {subscription_handler}')

            subscription_handler.verified_listings_count += 1
            subscription_handler.queued_listings_count -= 1

            logger.info(
                f'verified listings: {subscription_handler.verified_listings_count}\nqueued listings: {subscription_handler.queued_listings_count}')

            if subscription_handler.verified_listings_count == SubscriptionHandler.THRESHOLD:
                subscription_handler.is_expired = True
                logger.info(
                    f'subscription_handler has reached threshold: {subscription_handler.verified_listings_count} and is now expired!')

            subscription_handler.save()
            logger.info(
                f'verified listings: {subscription_handler.verified_listings_count}\nqueued listings: {subscription_handler.queued_listings_count}')

            # 2. Expire subscription logic
            subscription = subscribed_listing.subscription

            has_non_expired_handlers = subscription.subscription_handlers.filter(
                is_expired=False).exists()

            if not has_non_expired_handlers:
                subscription.is_expired = True
                subscription.save()
                logger.info(
                    f'Subscription with id: {subscription.pk} is now expired!')

            # end subscription life cycle

            logger.info(
                f'Status changed to verified for subscribed_listing with id {subscribed_listing_id}')
        else:
            logger.info(
                f'Cannot verify listing with status: {subscribed_listing.status}\nlisting pk: {subscribed_listing_id}')
    except SubscribedListing.DoesNotExist:
        logger.error(
            f'subscribed_listing does not exist for id: {subscribed_listing_id}')
