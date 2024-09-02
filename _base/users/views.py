from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from auths.decorators import role_required
from listings.models import RoomProfile, Region

# Create your views here.


@login_required
@role_required(['CREATOR'])
def get_creator(request):
    return render(request, 'users/creator.html')


@login_required
@role_required(['CLIENT'])
def get_client(request):

    subscriptions = request.user.subscriptions.filter(is_expired=False)

    # Get a queryset of all subscribed rooms across these subscriptions
    subscribed_rooms = RoomProfile.objects.filter(
        subscriptions__in=subscriptions
    ).distinct()

    subscribed_regions = Region.objects.filter(
        lodges__subscriptions__in=subscriptions
    ).distinct()

    context = {
        'subscribed_rooms': subscribed_rooms,
        'subscribed_regions': subscribed_regions
    }

    return render(request, 'users/client.html', context)
