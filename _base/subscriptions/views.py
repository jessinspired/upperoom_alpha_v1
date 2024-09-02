from django.shortcuts import render, redirect
from listings.models import School, Region, RoomProfile, Lodge
from django.views.decorators.http import require_http_methods
from .models import Subscription


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
    return subscribed_rooms


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
