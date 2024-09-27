from django.shortcuts import render, redirect, get_object_or_404
from listings.models import LodgeGroup, School, Region, RoomProfile, Lodge
from django.views.decorators.http import require_http_methods
from .models import Subscription, SubscribedListing, SubscriptionHandler
from core.views import handle_http_errors
import logging
from auths.decorators import role_required
from django.http import HttpResponse
from celery import current_app
from django_htmx.http import retarget
from django.db.models import F, OuterRef, Subquery, Exists
from django.db.models.functions import Random


# from messaging.tasks import send_creator_subscription_mail

logger = logging.getLogger('subscriptions')


@require_http_methods(['GET'])
def get_regions(request):
    school_id = request.GET.get('school')
    school = School.objects.get(pk=school_id)

    regions = school.regions.all()
    context = {
        'regions': regions
    }

    return render(
        request,
        'subscriptions/regions-partial.html',
        context
    )


def subscribe_for_listing(transaction):
    """
    Handle initial subscription when client pays
    """
    subscription = Subscription.objects.create(
        client=transaction.client,
        transaction=transaction
    )

    regions = transaction.regions.all()

    for region in regions:
        SubscriptionHandler.objects.create(
            subscription=subscription,
            region=region
        )
    logger.info(f'{regions.count()} subscription handler(s) created')

    # lodges = Lodge.objects.filter(region__in=regions)

    subscribed_rooms = subscription_algorithm(regions, subscription)

    subscription.subscribed_rooms.set(subscribed_rooms)
    return subscription, subscribed_rooms


def subscription_algorithm(regions, subscription):
    """
    Selects room profiles based on regions, room types, and price filters when a subscription is initiated.

    The algorithm selects rooms by applying filters such as room type and price range,
    and limits the selection to a maximum threshold (randomized) for each region.
    It creates a `SubscribedListing` for each room profile that matches the filters.

    Args:
        regions (QuerySet): A QuerySet of Region objects representing regions the client is interested in.
        subscription (Subscription): The subscription object, which contains the transaction and
                                     associated filters such as room types and price range.

    Returns:
        QuerySet: A combined QuerySet of all room profiles that matched the filters for the provided regions.

    Behavior:
        - The function iterates over the provided regions and retrieves lodges in each region.
        - It checks for room type filters and price range specified in the subscription's transaction.
        - It then selects room profiles that match the criteria, limiting the selection to a random sample
          up to the threshold (20 rooms by default).
        - For each matching room profile, a `SubscribedListing` is created.
        - The function updates the subscription handler with the count of queued listings and
          returns a QuerySet containing all selected room profiles.
    """
    all_room_profiles = RoomProfile.objects.none()

    logger.info(f'regions: {regions}, regions count {regions.count()}')
    min_price = subscription.transaction.min_price
    max_price = subscription.transaction.max_price
    filtered_room_types = subscription.transaction.room_types.all()

    logger.info(f'Max price: {max_price}, type: {type(max_price)}')
    logger.info(f'Room types filter: {filtered_room_types}')

    for region in regions:
        # get groups
        if filtered_room_types:
            chosen_groups = LodgeGroup.objects.filter(
                region=region,
                lodges__room_profiles__vacancy__gt=0,
                room_types__in=filtered_room_types
            ).distinct()
        else:
            chosen_groups = LodgeGroup.objects.filter(
                region=region,
                lodges__room_profiles__vacancy__gt=0
            ).distinct()

        # get lodges
        random_lodge_subquery = Lodge.objects.filter(
            group=OuterRef('pk'),
            room_profiles__vacancy__gt=0
        ).order_by(Random()).values('pk')[:1]

        groups_with_random_lodges = chosen_groups.annotate(
            random_lodge=Subquery(random_lodge_subquery)
        )

        lodges = Lodge.objects.filter(
            pk__in=groups_with_random_lodges.values('random_lodge'))

        # get room profile
        room_profiles_in_region = RoomProfile.objects.filter(
            lodge__in=lodges,
            vacancy__gt=0,
            price__gte=min_price,
            price__lte=max_price
        ).order_by('?')[:SubscriptionHandler.THRESHOLD]

        count = 0

        subscription_handler = SubscriptionHandler.objects.get(
            region=region,
            subscription=subscription
        )
        for room_profile in room_profiles_in_region:
            SubscribedListing.objects.create(
                subscription=subscription,
                subscription_handler=subscription_handler,
                room_profile=room_profile,
                creator=room_profile.lodge.creator,
                client=subscription.client
            )

            count += 1

        subscription_handler.queued_listings_count = count
        subscription_handler.save()

        all_room_profiles = all_room_profiles | room_profiles_in_region

    logger.info(f'Room profiles count: {all_room_profiles.count()}')
    return all_room_profiles


def get_subscribed_listings(request, pk):
    """
    Get all listings client subscribed for
    The link sent to the client is handled by this function

    Return: A html page containing all the listings for current subscription
    """
    try:
        subscription = Subscription.objects.get(pk=pk)
    except Subscription.DoesNotExist as e:
        logger.error(
            f'Cannot get subscribed listing with pk: {pk}, error: {e}')
        return handle_http_errors(request, 404)

    subscribed_listings = subscription.subscribed_listings.all()
    context = {
        'subscribed_listings': subscribed_listings
    }

    return render(
        request,
        'subscriptions/client/subscribed-listings.html',
        context
    )


def create_subscribed_listing(subscription):
    """
    NOT CURRENTLY IN USE!!!!
    """
    subscribed_listings = []
    creator_email_set = set()

    # check if subscribed listing already exists
    for room_profile in subscription.subscribed_rooms.all():
        subscribed_listing = SubscribedListing.objects.create(
            subscription=subscription,
            room_profile=room_profile,
            creator=room_profile.lodge.creator,
            client=subscription.client
        )
        subscribed_listings.append(subscribed_listing)
        creator_email_set.add(room_profile.lodge.creator.email)

    logger.info(
        f'subscribed listings listing successfully created for subscription {subscription.pk}'
    )

    creator_email_list = list(creator_email_set)

    # send_creator_subscription_mail(list(creator_email_set))

    return subscribed_listings, creator_email_list


@require_http_methods(['POST'])
@role_required(['CLIENT'])
def handle_occupied_report(request, pk):
    try:
        listing = SubscribedListing.objects.get(pk=pk)
    except SubscribedListing.DoesNotExist as e:
        logger.error(
            f'Subscribed listing with pk {pk} does not exist for occupied report\nError: {e}')

        return handle_http_errors(request, 404)

    if listing.status == SubscribedListing.Status.UNVERIFIED:
        listing.status = SubscribedListing.Status.PROBATION

        current_app.control.revoke(listing.status_task_id, terminate=True)
        listing.status_task_id = None
        listing.save()
        logger.info(
            f"Subscribed listing for client {listing.subscription.client.email}\n"
            f"Status updated: UNVERIFIED -> PROBATION\n"
            "status_task_id set to None."
        )

        subscription_handler = listing.subscription_handler
        if subscription_handler.queued_listings_count > 0:
            subscription_handler.queued_listings_count -= 1
            subscription_handler.save()

        context = {
            'listing': listing
        }
        return render(request, 'subscriptions/client/occupied-report-response.html', context)
    else:
        logger.info(
            f'Subscribed listing with status {listing.status} cannot be set to probation')

        context = {
            'messages': ['Listing needs to be unverified to be set to probation']
        }
        response = render(request, 'elements/response-modal.html', context)
        return retarget(response, '#global-response-modal')


def vacancy_update_algorithm(room_profile):
    """
    Updates vacancy status and determines the list of clients to notify about available room profiles.

    This function filters subscription handlers that are linked to the region of the given `room_profile`
    and that have not yet reached their listing threshold. It then checks whether the room profile's
    type and price fall within the filters set by each subscription's transaction. If they do, the function
    creates a `SubscribedListing`, updates the `queued_listings_count`, and collects the clients' emails
    for notification.

    Args:
        room_profile (RoomProfile): A `RoomProfile` instance representing the room whose vacancy status
                                    has been updated and should trigger notifications.

    Returns:
        list: A list of unique email addresses of clients who should receive updates based on their
              subscriptions and transaction preferences.

    Behavior:
        - Filters `SubscriptionHandler` objects linked to the region of the `room_profile`, ensuring
          that the handlers are not expired and have not reached the listing threshold.
        - For each filtered handler, checks if the `room_profile` matches the subscribed room types and
          falls within the price range of the associated transaction.
        - If the room profile matches the filters, creates a `SubscribedListing`, updates the
          `queued_listings_count`, and saves the changes.
        - Gathers and returns the unique email addresses of clients for sending updates.
    """
    region = room_profile.lodge.region

    subscription_handlers = SubscriptionHandler.objects.filter(
        region=region,
        is_expired=False
    ).annotate(
        total_listings=F('queued_listings_count') +
        F('verified_listings_count')
    ).exclude(
        total_listings=SubscriptionHandler.THRESHOLD
    )
    logger.info(f'Subscription handlers filtered')

    clients_email_set = set()
    for subscription_handler in subscription_handlers:
        transaction = subscription_handler.subscription.transaction

        # implement room type filter
        chosen_room_types = transaction.room_types.all()
        if chosen_room_types.exists() and room_profile.room_type not in chosen_room_types:
            continue

        if room_profile.price > transaction.max_price or room_profile.price < transaction.min_price:
            continue

        SubscribedListing.objects.create(
            subscription=subscription_handler.subscription,
            subscription_handler=subscription_handler,
            room_profile=room_profile,
            creator=room_profile.lodge.creator,
            client=subscription_handler.subscription.client
        )
        subscription_handler.queued_listings_count += 1
        subscription_handler.save()

        clients_email_set.add(subscription_handler.subscription.client.email)

        logger.info(
            f'queued listings is {subscription_handler.queued_listings_count} for subscription handler with pk {subscription_handler.pk}')

    logger.info(f'Sending vacancy updates to clients: {clients_email_set}')

    return list(clients_email_set)
