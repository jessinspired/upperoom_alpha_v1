from django.shortcuts import render, redirect, get_object_or_404
from listings.models import School, Region, RoomProfile, Lodge
from django.views.decorators.http import require_http_methods
from .models import Subscription, SubscribedListing
from core.views import handle_http_errors
import logging
from auths.decorators import role_required
from django.http import HttpResponse
from celery import current_app
from django_htmx.http import retarget

# from messaging.tasks import send_creator_subscription_mail

logger = logging.getLogger('subscriptions')


@require_http_methods(['GET'])
def get_regions(request):
    school_id = request.GET.get('schools')
    school = School.objects.get(pk=school_id)

    regions = school.regions.all()
    print(regions)
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
    lodges = Lodge.objects.filter(region__in=regions)

    subscribed_rooms = subscription_algorithm(lodges)

    subscription.subscribed_rooms.set(subscribed_rooms)
    return subscription, subscribed_rooms


def subscription_algorithm(lodges):
    """
    Algorithm to select rooms, using basic randomization for now.
    This function limits the selection to a maximum of 20 randomly chosen rooms.
    """
    vacant_rooms = RoomProfile.objects.filter(
        lodge__in=lodges,
        vacancy__gt=0
    ).order_by('?')[:20]

    return vacant_rooms


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
            f'Subscribed listing status changed from unverified to probation for pk: {pk}\ntask_status_id for subscribed_listing set to None')

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
