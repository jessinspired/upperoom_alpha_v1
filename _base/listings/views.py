from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from auths.decorators import role_required
from .forms import LodgeImageForm, LodgeRegistrationForm, RoomProfileForm, RoomProfileImageForm
from listings.models import Landmark, Lodge, LodgeGroup, LodgeImage, Region, RoomType, RoomProfile, School, State
from django.forms import formset_factory
from django.views.decorators.http import require_http_methods
from django_htmx.http import HttpResponseClientRefresh
import logging
from django.contrib import messages
from payments.models import CreatorTransferInfo
from core.views import handle_http_errors
from thefuzz import fuzz
import re
from django.shortcuts import get_object_or_404


logger = logging.getLogger('listings')


# @role_required(['CREATOR'])
def group_lodge_by_name(lodge):
    if not lodge.name:
        return None

    if lodge.landmark:
        lodges_in_region = Lodge.objects.filter(
            landmark=lodge.landmark).exclude(id=lodge.id)
    else:
        lodges_in_region = Lodge.objects.filter(
            region=lodge.region).exclude(id=lodge.id)

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
        name=group_name
    )
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

    if lodge.name:
        group_lodge_by_name(lodge)

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


class RoomImageUploadView(View):
    def get(self, request):
        form = RoomProfileImageForm()
        return render(request, 'listings/upload-room-image.html', {'form': form})

    def post(self, request):
        form = RoomProfileImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Room image uploaded successfully!')
            return redirect('upload_room_image')  # Redirect to the same or another page
        return render(request, 'listings/upload-room-image.html', {'form': form})
    

class LodgeImageUploadView(View):
    def get(self, request):
        lodge_id = request.GET.get('lodge_id')
        
        # Fetch existing images for FrontView and BackView
        front_view = LodgeImage.objects.filter(lodge__id=lodge_id, category=LodgeImage.Category.FRONT_VIEW).first()
        back_view = LodgeImage.objects.filter(lodge__id=lodge_id, category=LodgeImage.Category.BACK_VIEW).first()
        
        # Fetch all images for OtherViews
        other_views = LodgeImage.objects.filter(lodge__id=lodge_id, category=LodgeImage.Category.OTHER_VIEWS)

        front_form = LodgeImageForm(instance=front_view)
        back_form = LodgeImageForm(instance=back_view)
        
        return render(request, 'listings/upload-lodge-image.html', {
            'front_form': front_form,
            'back_form': back_form,
            'other_views': other_views,
            'lodge_id': lodge_id
        })

    def post(self, request):
        lodge_id = request.POST.get('lodge_id')
        
        # Fetch existing images for FrontView and BackView
        front_view = LodgeImage.objects.filter(lodge__id=lodge_id, category=LodgeImage.Category.FRONT_VIEW).first()
        back_view = LodgeImage.objects.filter(lodge__id=lodge_id, category=LodgeImage.Category.BACK_VIEW).first()
        
        if 'upload_front' in request.POST:
            if front_view:
                front_form = LodgeImageForm(request.POST, request.FILES, instance=front_view)
            else:
                front_form = LodgeImageForm(request.POST, request.FILES)
            
            if front_form.is_valid():
                front_form.save()
                messages.success(request, 'Front view image uploaded/updated successfully!')
            else:
                messages.error(request, 'Error uploading front view image.')

        if 'upload_back' in request.POST:
            if back_view:
                back_form = LodgeImageForm(request.POST, request.FILES, instance=back_view)
            else:
                back_form = LodgeImageForm(request.POST, request.FILES)
            
            if back_form.is_valid():
                back_form.save()
                messages.success(request, 'Back view image uploaded/updated successfully!')
            else:
                messages.error(request, 'Error uploading back view image.')

        if 'upload_other' in request.POST:
            # Handle multiple uploads for OtherViews
            other_images = request.FILES.getlist('other_images')
            for image in other_images:
                lodge_image = LodgeImage(lodge_id=lodge_id, image=image, category=LodgeImage.Category.OTHER_VIEWS)
                lodge_image.save()
                messages.success(request, f'Other view image uploaded successfully!')

        return redirect('upload_lodge_image', lodge_id=lodge_id)
    
# end lodge registration
