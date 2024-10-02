from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from auths.decorators import role_required
from listings.models import Region, RoomType, School, State
from payments.models import Transaction
from subscriptions.models import SubscribedListing

# Create your views here.


@role_required(['CREATOR'])
def get_creator(request):

    unverified_listings = request.user.client_subscribed_listings.filter(
        status=SubscribedListing.Status.UNVERIFIED)

    verified_listings = request.user.client_subscribed_listings.filter(
        status=SubscribedListing.Status.VERIFIED)

    probation_listings = request.user.client_subscribed_listings.filter(
        status=SubscribedListing.Status.PROBATION)

    rejected_listings = request.user.client_subscribed_listings.filter(
        status=SubscribedListing.Status.REJECTED)

    context = {
        'is_dashboard': True,
        'unverified_listings': unverified_listings,
        'verified_listings': verified_listings,
        'probation_listings': probation_listings,
        'rejected_listings': rejected_listings,
    }

    return render(request, 'users/creator/dashboard.html', context)


@role_required(['CLIENT'])
def get_client(request):

    subscriptions = request.user.subscriptions.filter(is_expired=False)

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
    expired_subscriptions = request.user.subscriptions.filter(is_expired=True)

    context = {
        'unverified_listings': unverified_listings,
        'verified_listings': verified_listings,
        'probation_listings': probation_listings,
        'rejected_listings': rejected_listings,
        'settled_listings': settled_listings,
        'subscribed_regions': subscribed_regions,
        'incomplete_transactions': incomplete_transactions,
        'complete_transactions': complete_transactions,
        'active_subscriptions': active_subscriptions,
        'expired_subscriptions': expired_subscriptions
    }

    return render(request, 'users/client/dashboard.html', context)


@role_required(['CLIENT'])
def get_client_subscriptions(request):
    active_subscriptions = request.user.subscriptions.filter(
        is_expired=False).order_by('-created_at')
    expired_subscriptions = request.user.subscriptions.filter(is_expired=True)

    context = {
        'active_subscriptions': active_subscriptions,
        'expired_subscriptions': expired_subscriptions
    }
    return render(request, 'users/client/subscriptions.html', context)


@role_required(['CREATOR'])
def get_creator_listings(request):
    context = {
        'is_listings': True,
        'states': State.objects.all(),
        'room_types': RoomType.objects.all()
    }

    return render(request, 'users/creator/listings.html', context)


@role_required(['CREATOR'])
def get_creator_payments(request):
    context = {
        'is_earnings': True
    }
    return render(request, 'users/creator/payments.html', context)
