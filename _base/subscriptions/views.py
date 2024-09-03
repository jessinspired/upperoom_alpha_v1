from django.shortcuts import render, redirect, get_object_or_404
from listings.models import School, Region, RoomProfile, Lodge
from django.views.decorators.http import require_http_methods
from .models import Subscription
from core.views import handle_http_errors


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


def get_order_summary(request):
    if request.method != 'POST':
        return redirect('get_home')
    regions_pk_list = request.POST.getlist('regions')

    if not regions_pk_list:
        # bad request
        return redirect('get_home')

    try:
        regions = []
        for pk in regions_pk_list:
            region = Region.objects.get(pk=pk)
            regions.append(region)
    except:
        return redirect('get_home')

    # regions = list(School.objects.get(abbr='UNIPORT').regions.all())

    context = {
        'regions': regions,
        'amount': 1500 * len(regions)
    }

    return render(request, 'subscriptions/order-summary.html', context)


def subscribe_for_listing(transaction):
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
    except Subscription.DoesNotExist:
        return handle_http_errors(request, 404)

    subscribed_rooms = subscription.subscribed_rooms.all()
    context = {
        'subscribed_rooms': subscribed_rooms
    }

    return render(
        request,
        'subscriptions/subscribed-listings.html',
        context
    )
