from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django_htmx.http import HttpResponseClientRefresh
from django.contrib import messages

from thefuzz import fuzz
import logging
import re

from payments.models import CreatorTransferInfo
from auths.decorators import role_required
from .forms import RoomProfileForm
from listings.models import Landmark, Lodge, LodgeGroup, Region, RoomType, RoomProfile, School, State
from core.views import handle_http_errors
from payments.utils import convert_price_to_decimal
from decimal import Decimal


logger = logging.getLogger('listings')


# @role_required(['CREATOR'])
def group_lodge_by_name(lodge):
    if not lodge.name:
        return None

    if lodge.landmark:
        lodges_in_region = Lodge.objects.filter(
            landmark=lodge.landmark).exclude(id=lodge.id)
        landmark = lodge.landmark
    else:
        lodges_in_region = Lodge.objects.filter(
            region=lodge.region).exclude(id=lodge.id)
        landmark = None

    threshold = 95

    for other_lodge in lodges_in_region:
        similarity_score = fuzz.ratio(
            lodge.name.lower(), other_lodge.name.lower())
        if similarity_score >= threshold:
            lodge.group = other_lodge.group
            lodge.save()

            logger.info(f'existing group: {other_lodge.group.name}')

            return {
                'similar_lodge': other_lodge,
                'similarity_score': similarity_score,
                'group': other_lodge.group,
                'is_new_group': False
            }

    region_name = re.sub(r'\s+', '_', lodge.region.name.lower())
    lodge_name = re.sub(r'\s+', '_', lodge.name.lower())
    group_name = f'{region_name}__{lodge_name}'

    new_group = LodgeGroup.objects.create(
        name=group_name,
        region=lodge.region,
        landmark=landmark
    )
    new_group.room_types.set(lodge.room_types.all())

    lodge.group = new_group
    lodge.save()

    logger.info(f'new group: {new_group.name}')

    return {
        'group': new_group,
        'is_new_group': True,
        'similar_lodge': None,
        'similarity_score': None,
    }


@role_required(['CREATOR'])
def set_lodge_location(request, lodge_pk):
    if lodge.creator != request.user:
        logger.error(f"User cannot set lodge location: Forbidden")
        messages.error(request, f'Forbidden to set location')
        return HttpResponseClientRefresh()

    try:
        lodge = Lodge.objects.get(pk=lodge_pk)
        longitude = Decimal(request.POST.get('longitude'))
        latitude = Decimal(request.POST.get('latitude'))
    except Exception as e:
        logger.error(
            f"Failed to set location for lodge with pk: {lodge_pk}, exception: {e}")
        messages.error(request, f'Lodge does not exist to set location')
        return HttpResponseClientRefresh()

    lodge.latitude = latitude
    lodge.longitude = longitude
    lodge.save()

    messages.success(request, f'Location set')
    maps_url = f"https://www.google.com/maps/@?api=1&map_action=map&center={latitude},{longitude}&zoom=15"
    return HttpResponse(f"<a href='{maps_url}'>View in map</a>")


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

        return redirect('creator_transfer_info')

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

    if lodge.name:
        group_lodge_by_name(lodge)

    messages.success(
        request, f'Quickly set up room profiles so clients can get your vacancy updates')
    redirect_url = reverse('get_lodge_profile', args=[lodge.pk])
    return redirect(redirect_url)


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
        messages.error(request, f'room profile does not exist')
        logger.error('room profile does not exist')
        return HttpResponseClientRefresh()

    form = RoomProfileForm(request.POST)
    if form.is_valid():
        form.save(room_profile)
    else:
        logger.error(f'Update room profile error: {form.errors.items()}')
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{error}')
        return HttpResponseClientRefresh()

    messages.success(
        request, f'{room_profile.room_type.get_name_display()} successfully updated!')
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


# def upload_lodge_image(request, lodge_id):
#     lodge = get_object_or_404(Lodge, id=lodge_id)

#     if request.method == 'POST':
#         form = LodgeImageForm(request.POST, request.FILES)
#         if form.is_valid():
#             lodge_image = form.save(commit=False)
#             lodge_image.lodge = lodge
#             lodge_image.save()
#             return redirect('get_lodge_profile', pk=lodge.id)
#     else:
#         form = LodgeImageForm()

#     return render(request, 'listings/upload-lodge-image.html', {'form': form, 'lodge': lodge})


# def upload_room_profile_image(request, room_profile_id):
#     room_profile = get_object_or_404(RoomProfile, id=room_profile_id)

#     if request.method == 'POST':
#         form = RoomProfileImageForm(request.POST, request.FILES)
#         if form.is_valid():
#             room_profile_image = form.save(commit=False)
#             room_profile_image.room_profile = room_profile
#             room_profile_image.save()
#             return redirect('get_lodge_profile', pk=room_profile.lodge.id)
#     else:
#         form = RoomProfileImageForm()

#     return render(request, 'listings/upload-room-profile-image.html', {'form': form, 'room_profile': room_profile})


def get_vacancy_search_result(request):
    regions_pk_list = request.GET.getlist('regions')
    room_types_pk_list = request.GET.getlist('room-type')

    school_pk = request.GET.get('school')

    if not School.objects.filter(pk=school_pk).exists():
        logger.error(f'No school exists for pk {school_pk}')
        return redirect('get_home')

    if not regions_pk_list:
        logger.error(
            'Bad Request (400): No list of regions to get order summary for')

        messages.error(request, "Select at least one region")
        return redirect('get_home')

    all_room_profiles = RoomProfile.objects.none()

    try:
        regions = []
        for pk in regions_pk_list:
            region = Region.objects.get(pk=pk)
            regions.append(region)

        filtered_room_types = []
        if room_types_pk_list:
            for pk in room_types_pk_list:
                room_type = RoomType.objects.get(pk=pk)
                filtered_room_types.append(room_type)

        min_price = request.GET.get('min-price')
        max_price = request.GET.get('max-price')

        min_price, max_price = convert_price_to_decimal(min_price, max_price)

    except Exception as e:
        logger.error(f"Couldn't retrieve search results with error: {e}")
        return redirect('get_home')

    vacancy_statistics = {}
    for region in regions:
        # get groups
        if filtered_room_types:
            chosen_groups = LodgeGroup.objects.filter(
                region=region,
                lodges__room_profiles__vacancy__gt=0,
                room_types__in=filtered_room_types
            ).distinct()
        else:
            chosen_groups = LodgeGroup.objects.filter(
                region=region,
                lodges__room_profiles__vacancy__gt=0
            ).distinct()
        logger.info(f'chosen groups {chosen_groups}')

        if not chosen_groups:
            vacancy_statistics[region.name] = 0
            continue

        # get a random lodge from group
        lodges = []
        for group in chosen_groups:
            logger.info(f'current group {group}')
            random_lodge = group.lodges.filter(
                room_profiles__vacancy__gt=0,
                room_types__in=filtered_room_types
            ).order_by('?').first()

            if random_lodge:
                lodges.append(random_lodge)
                logger.info(f'random lodge: {random_lodge}')

        # get room profiles
        try:
            chosen_room_profiles = RoomProfile.objects.filter(
                lodge__in=lodges,
                vacancy__gt=0,
                price__gte=min_price,
                price__lte=max_price,
                room_type__in=filtered_room_types
            )
        except Exception as e:
            logger.error(f'Cannot get chosen room profile, error: {e}')
            messages.error(request, f'Cannot get search results')
            return HttpResponseClientRefresh()
        vacancy_statistics[region.name] = chosen_room_profiles.count()

        all_room_profiles = all_room_profiles | chosen_room_profiles

    logger.info(f'Room profiles count: {all_room_profiles.count()}')

    context = {
        'total_vacancy': all_room_profiles.count(),
        'vacancy_statistics': vacancy_statistics
    }

    return render(request, 'messages/vacancy-search-result.html', context)
