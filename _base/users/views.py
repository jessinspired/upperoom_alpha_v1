from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from auths.decorators import role_required
from listings.models import RoomProfile, Region
from payments.models import Transaction
from listings.forms import LodgeRegistrationForm, RoomProfileForm


# Create your views here.


@role_required(['CREATOR'])
def get_creator(request):
    subscribed_listings = request.user.client_subscribed_listings.all()

    context = {
        'subscribed_listings': subscribed_listings
    }

    return render(request, 'users/creator/dashboard.html', context)


@role_required(['CLIENT'])
def get_client(request):

    subscriptions = request.user.subscriptions.filter(is_expired=False)

    # subscribed_rooms = RoomProfile.objects.filter(
    #     subscriptions__in=subscriptions
    # ).distinct()

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

    incomplete_transactions = request.user.transactions.filter(
        is_fully_paid=False)

    complete_transactions = request.user.transactions.filter(
        is_fully_paid=True)

    active_subscriptions = request.user.subscriptions.filter(is_expired=False)

    context = {
        'unverified_listings': unverified_listings,
        'verified_listings': verified_listings,
        'probation_listings': probation_listings,
        'rejected_listings': rejected_listings,
        'settled_listings': settled_listings,
        'subscribed_regions': subscribed_regions,
        'incomplete_transactions': incomplete_transactions,
        'complete_transactions': complete_transactions,
        'active_subscriptions': active_subscriptions
    }

    return render(request, 'users/client/dashboard.html', context)


@role_required(['CLIENT'])
def get_client_subscriptions(request):
    active_subscriptions = request.user.subscriptions.filter(is_expired=False)

    context = {
        'active_subscriptions': active_subscriptions
    }
    return render(request, 'users/client/subscriptions.html', context)


@role_required(['CREATOR'])
def get_creator_listings(request):
    lodge_registration_form = LodgeRegistrationForm()

    context = {
        'lodge_registration_form': lodge_registration_form
    }

    return render(request, 'users/creator/listings.html', context)
