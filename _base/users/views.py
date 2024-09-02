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
    return render(request, 'users/creator.html')


@login_required
@role_required(['CLIENT'])
def get_client(request):

    subscriptions = request.user.subscriptions.filter(is_expired=False)

    subscribed_rooms = RoomProfile.objects.filter(
        subscriptions__in=subscriptions
    ).distinct()

    transactions = Transaction.objects.filter(subscription__in=subscriptions)
    subscribed_regions = Region.objects.filter(
        transactions__in=transactions).distinct()

    context = {
        'subscribed_rooms': subscribed_rooms,
        'subscribed_regions': subscribed_regions
    }

    return render(request, 'users/client.html', context)
