from django.shortcuts import render, redirect
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404
from django.views.decorators.http import require_http_methods
from django_htmx.http import HttpResponseClientRefresh
from django.contrib import messages

from thefuzz import fuzz
import logging
import re

from payments.models import CreatorTransferInfo
from auths.decorators import role_required
from .forms import  RoomProfileForm
from listings.models import Landmark, Lodge, LodgeGroup, LodgeImage, Region, RoomProfileImage, RoomType, RoomProfile, School, State
from core.views import handle_http_errors
from .serializers import LodgeImageSerializer, RoomProfileImageSerializer


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


# LodgeImage Views
class LodgeImageView(APIView):

    def get(self, request, lodge_id, category=None):
        """Retrieve images for a particular lodge and optional category (FRONT_VIEW, BACK_VIEW, OTHER_VIEWS)"""
        lodge = get_object_or_404(Lodge, id=lodge_id)
        if category:
            images = LodgeImage.objects.filter(lodge=lodge, category=category)
        else:
            images = LodgeImage.objects.filter(lodge=lodge)

        serializer = LodgeImageSerializer(images, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, lodge_id):
        """Upload an image for a lodge, respecting the rule for one front and back view image."""
        lodge = get_object_or_404(Lodge, id=lodge_id)
        category = request.data.get('category')

        # Check for category constraints
        if category in [LodgeImage.Category.FRONT_VIEW, LodgeImage.Category.BACK_VIEW]:
            if LodgeImage.objects.filter(lodge=lodge, category=category).exists():
                return Response(
                    {"detail": f"{category} image already exists for this lodge."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Save the image
        data = request.data.copy()
        data['lodge'] = lodge.id
        serializer = LodgeImageSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, lodge_id, image_id):
        """Update an existing image for a lodge"""
        lodge = get_object_or_404(Lodge, id=lodge_id)
        image = get_object_or_404(LodgeImage, id=image_id, lodge=lodge)
        serializer = LodgeImageSerializer(image, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, lodge_id, image_id):
        """Delete an image from a lodge"""
        lodge = get_object_or_404(Lodge, id=lodge_id)
        image = get_object_or_404(LodgeImage, id=image_id, lodge=lodge)
        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# RoomProfileImage Views
class RoomProfileImageView(APIView):

    def get(self, request, room_profile_id):
        """Retrieve images for a particular room profile"""
        room_profile = get_object_or_404(RoomProfile, id=room_profile_id)
        images = RoomProfileImage.objects.filter(room_profile=room_profile)
        serializer = RoomProfileImageSerializer(images, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, room_profile_id):
        """Upload an image for a room profile"""
        room_profile = get_object_or_404(RoomProfile, id=room_profile_id)
        data = request.data.copy()
        data['room_profile'] = room_profile.id

        serializer = RoomProfileImageSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, room_profile_id, image_id):
        """Update an existing image for a room profile"""
        room_profile = get_object_or_404(RoomProfile, id=room_profile_id)
        image = get_object_or_404(RoomProfileImage, id=image_id, room_profile=room_profile)
        serializer = RoomProfileImageSerializer(image, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, room_profile_id, image_id):
        """Delete an image from a room profile"""
        room_profile = get_object_or_404(RoomProfile, id=room_profile_id)
        image = get_object_or_404(RoomProfileImage, id=image_id, room_profile=room_profile)
        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)