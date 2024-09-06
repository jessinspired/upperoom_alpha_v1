from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from auths.decorators import role_required
from listings.models import RoomProfile, Region
from payments.models import Transaction

# Create your views here.


@login_required
@role_required(['CREATOR'])
def get_creator(request):
    subscribed_listings = request.user.client_subscribed_listings.all()

    context = {
        'subscribed_listings': subscribed_listings
    }

    return render(request, 'users/creator.html', context)


@login_required
@role_required(['CLIENT'])
def get_client(request):

    subscriptions = request.user.subscriptions.filter(is_expired=False)

    subscribed_rooms = RoomProfile.objects.filter(
        subscriptions__in=subscriptions
    ).distinct()

    from subscriptions.models import SubscribedListing
    unverified_listings = request.user.subscribed_listings.filter(
        status=SubscribedListing.Status.UNVERIFIED)

    verified_listings = request.user.subscribed_listings.filter(
        status=SubscribedListing.Status.VERIFIED)

    probation_listings = request.user.subscribed_listings.filter(
        status=SubscribedListing.Status.PROBATION)

    rejected_listings = request.user.subscribed_listings.filter(
        status=SubscribedListing.Status.REJECTED)

    settled_listings = request.user.subscribed_listings.filter(
        status=SubscribedListing.Status.SETTLED)

    transactions = Transaction.objects.filter(subscription__in=subscriptions)
    subscribed_regions = Region.objects.filter(
        transactions__in=transactions).distinct()

    context = {
        'unverified_listings': unverified_listings,
        'verified_listings': verified_listings,
        'probation_listings': probation_listings,
        'rejected_listings': rejected_listings,
        'settled_listings': settled_listings,
        'subscribed_regions': subscribed_regions
    }

    return render(request, 'users/client.html', context)
