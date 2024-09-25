from django.shortcuts import render, redirect
from django.urls import reverse
from auths.decorators import role_required
from .forms import LodgeRegistrationForm, RoomProfileForm
from listings.models import Landmark, Lodge, Region, RoomType, RoomProfile, School, State
from django.forms import formset_factory
from django.views.decorators.http import require_http_methods
from django_htmx.http import HttpResponseClientRefresh
import logging
from django.contrib import messages
from payments.models import CreatorTransferInfo
from core.views import handle_http_errors


logger = logging.getLogger('listings')


@role_required(['CREATOR'])
def register_lodge(request):
    if request.method != 'POST':
        return redirect('get_creator_listings')

    try:
        request.user.transfer_profile
    except CreatorTransferInfo.DoesNotExist as e:
        messages.error(
            request, 'Add payment details in "Earnings" section to register a lodge')
        logger.error(
            f'Creator transfer info does not exist for creator with email {request.user.email}\nError: {e}')
        if request.htmx:
            return HttpResponseClientRefresh()
        return redirect('get_creator_listings')

    name = request.POST.get('name')
    alias = request.POST.get('alias')
    phone_number = request.POST.get('phone_number')
    address = request.POST.get('address')
    state_pk = request.POST.get('state')
    school_pk = request.POST.get('school')
    region_pk = request.POST.get('region')
    landmark_pk = request.POST.get('landmark')
    room_types = request.POST.getlist('room-type')

    # do form validation here and error feedback (if necessary)
    region = Region.objects.get(pk=region_pk)

    try:
        landmark = Landmark.objects.get(pk=landmark_pk)
    except Landmark.DoesNotExist as e:
        landmark = None

    lodge = Lodge(
        name=name.title(),
        alias=alias.title(),
        phone_number=phone_number,
        address=address,
        state=region.state,
        school=region.school,
        region=region,
        creator=request.user,
        landmark=landmark
    )

    lodge.save()
    lodge.room_types.set(room_types)

    for room_type in lodge.room_types.all():
        RoomProfile.objects.create(
            lodge=lodge,
            room_type=room_type
        )

    redirect_url = reverse('get_lodge_profile', args=[lodge.pk])
    return redirect(redirect_url)

    # lodge_form = LodgeRegistrationForm(request.POST, request.FILES)
    # if lodge_form.is_valid():
    #     lodge = lodge_form.save(creator=request.user)

    #     logger.info(f'New lodge registered with pk: {lodge.pk}')

    #     messages.success(
    #         request, 'Lodge successfully registered!\nClick on lodge name to update price and vacancy')
    #     if request.htmx:
    #         # change later to dynamically partials
    #         return HttpResponseClientRefresh()
    #         # return render(request, 'listings/creator/register-lodge-response.html')
    #     return redirect('get_creator_listings')
    # else:
    #     for field, errors in lodge_form.errors.items():
    #         for error in errors:
    #             messages.error(request, f'{error}')
    #     if request.htmx:
    #         return HttpResponseClientRefresh()
    #     return redirect('get_creator_listings')


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


# lodge registration views
def get_schools(request):
    state_pk = request.GET.get('state')
    if not state_pk:
        logger.warning(f'Bad request, No state id given')
        return handle_http_errors(request, 400)

    state = State.objects.get(pk=state_pk)
    if not state:
        logger.error(f'Not found, State not found for pk {state_pk}')
        return handle_http_errors(request, 404)

    schools = state.schools.all()

    context = {
        'schools': schools
    }

    return render(
        request,
        'listings/creator/schools-select.html',
        context
    )


def get_regions_select(request):
    school_pk = request.GET.get('school')
    if not school_pk:
        logger.warning(f'Bad request, No school id given')
        return handle_http_errors(request, 400)

    school = School.objects.get(pk=school_pk)
    if not school:
        logger.error(f'Not found, school not found for pk {school_pk}')
        return handle_http_errors(request, 404)

    regions = school.regions.all()

    context = {
        'regions': regions
    }

    return render(
        request,
        'listings/creator/regions-select.html',
        context
    )


def get_landmarks_select(request):
    region_pk = request.GET.get('region')
    if not region_pk:
        logger.warning(f'Bad request, No region id given')
        return handle_http_errors(request, 400)

    region = Region.objects.get(pk=region_pk)
    if not region:
        logger.error(f'Not found, region not found for pk {region_pk}')
        return handle_http_errors(request, 404)

    landmarks = region.landmarks.all()

    context = {
        'landmarks': landmarks
    }

    return render(
        request,
        'listings/creator/landmarks-select.html',
        context
    )


# end lodge registration
