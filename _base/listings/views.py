from django.shortcuts import render, redirect
from auths.decorators import role_required
from .forms import LodgeRegistrationForm, RoomProfileForm
from listings.models import Lodge, RoomType, RoomProfile
from django.forms import formset_factory
from django.views.decorators.http import require_http_methods


@role_required(['CREATOR'])
def register_lodge(request):
    if request.method == 'POST':
        lodge_form = LodgeRegistrationForm(request.POST, request.FILES)
        if lodge_form.is_valid():
            lodge = lodge_form.save(creator=request.user)
            return redirect('get_creator')

            # url = reverse('lodge_profile', args=[lodge.id])
            # return redirect(url)
    else:
        form = LodgeRegistrationForm()

    context = {
        'form': form
    }
    template = 'listings/register-lodge.html'

    return render(request, template, context)


@role_required(['CREATOR'])
def get_lodge_profile(request, pk):
    lodge = Lodge.objects.get(pk=pk)

    rooms_dict = {
        profile.room_type.get_name_display(): RoomProfileForm(
            initial=profile.__dict__,
            instance=profile)
        for profile in lodge.room_profiles.all()
    }

    unavailable_room_types = RoomType.objects.exclude(lodges=lodge)

    context = {
        'lodge': lodge,
        'rooms_dict': rooms_dict,
        'unavailable_room_types': unavailable_room_types
    }
    return render(
        request,
        'listings/lodge-profile.html',
        context
    )


@require_http_methods(["POST"])
@role_required(['CREATOR'])
def update_room_profile(request, pk):
    room_profile = RoomProfile.objects.get(pk=pk)

    if not room_profile:
        # handle 404 here
        pass  # add logic here

    form = RoomProfileForm(request.POST)
    if form.is_valid():
        form.save(room_profile)

    return redirect('get_lodge_profile', pk=room_profile.lodge.pk)
