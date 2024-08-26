#!/usr/bin/env python3
'''listings models'''
# the 3 commented imports are for async image deleting
# import aiohttp
# import asyncio
# from decouple import config
from core.models import BaseModel
import os

from django.db import models
from django.core.exceptions import ValidationError, SuspiciousFileOperation
# from media.image_path_handler import *
# from media.image_path_handler.script import default_logo_cdn
from users.models import Client, Creator
# from cloudinary_storage.storage import MediaCloudinaryStorage
from django.utils import timezone
# import media.image_path_handler as media
# import cloudinary
# from cloudinary import CloudinaryImage

from django.db.models.signals import pre_delete
from django.dispatch import receiver
# from ckeditor.fields import RichTextField


class RoomType(BaseModel):
    class Type(models.TextChoices):
        ONE_ROOM = 'ONE_ROOM', 'One Room'
        SELF_CONTAINED = 'SELF_CONTAINED', 'Self Contained'
        ONE_BEDROOM = 'ONE_BEDROOM', 'One Bedroom'
        TWO_BEDROOMS = 'TWO_BEDROOMS', 'Two Bedrooms'
        THREE_BEDROOMS = 'THREE_BEDROOMS', 'Three Bedrooms'

    VALID_TYPES = (
        "ONE_ROOM",
        "SELF_CONTAINED",
        "ONE_BEDROOM",
        "TWO_BEDROOMS",
        "THREE_BEDROOMS"
    )

    name = models.CharField(
        max_length=150,
        choices=Type.choices,
        default=None
    )

    def __str__(self):
        return self.get_name_display()

    def clean(self):
        if self.name not in RoomType.VALID_TYPES:
            e = f"Room Type - '{self.name}' is not a valid RoomType"
            raise ValidationError(e)


class State(BaseModel):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class School(BaseModel):
    name = models.CharField(max_length=150)
    state = models.ForeignKey(
        State,
        on_delete=models.CASCADE,
        related_name='schools'
    )
    abbr = models.CharField(max_length=30, null=True)

    subscribed_clients = models.ManyToManyField(
        Client,
        related_name='subscribed_schools'
    )

    def __str__(self):
        return self.name


class Area(BaseModel):
    name = models.CharField(max_length=150)

    state = models.ForeignKey(
        State,
        on_delete=models.CASCADE,
        related_name='areas',
        default=None
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='areas',
        null=True,
        blank=True
    )

    subscribed_clients = models.ManyToManyField(
        Client,
        related_name='subscribed_areas'
    )

    def __str__(self):
        return self.name


class Landmark(BaseModel):
    name = models.CharField(max_length=150)

    area = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        related_name='landmarks',
        default=None
    )

    state = models.ForeignKey(
        State,
        on_delete=models.CASCADE,
        related_name='landmarks',
        default=None
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='landmarks',
        # default=None
        null=True,
        blank=True
    )

    subscribed_clients = models.ManyToManyField(
        Client,
        related_name='subscribed_landmarks'
    )

    def __str__(self):
        return self.name


class Lodge(BaseModel):
    '''models for lodges
    Args:
        models (BaseModel): Built-in django model
    '''
    name = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    # for creators to identify nameless lodges in dashboard
    alias = models.CharField(
        max_length=500,
        null=True,
        blank=True
    )

    info = models.JSONField(null=True, blank=True)

    phone_number = models.CharField(
        max_length=20,
        default=None
    )

    landmark = models.ForeignKey(
        Landmark,
        on_delete=models.CASCADE,
        related_name='lodges',
        null=True,
        blank=True
    )

    area = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        related_name='lodges',
        default=None
    )

    state = models.ForeignKey(
        State,
        on_delete=models.CASCADE,
        related_name='lodges',
        default=None
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='lodges',
        default=None
    )

    room_types = models.ManyToManyField(
        'listings.RoomType', related_name='lodges'
    )

    creator = models.ForeignKey(
        Creator,
        on_delete=models.CASCADE,
        related_name='lodges',
        default=None
    )

    # clients_inquired_for_vacancy = models.ManyToManyField(
    #     Client,
    #     related_name='lodges_inquired_for_vacancy',
    # )

    def __str__(self):
        return self.name


# class LodgeImage(BaseModel, ImageOptimizationModel):
#     image = models.ImageField(
#         upload_to=get_upload_path_lodge,
#         default=default_lodge_image_cdn,
#         storage=MediaCloudinaryStorage(),
#         null=True,
#         blank=True,
#         max_length=1000,
#     )

#     lodge = models.ForeignKey(
#         Lodge, on_delete=models.CASCADE, related_name='images')

#     class Meta(BaseModel.Meta, ImageOptimizationModel.Meta):
#         pass

#     def __str__(self):
#         return self.image.name

#     def delete(self, *args, **kwargs):
#         cloudinary.uploader.destroy(self.image.name)
#         super(LodgeImage, self).delete(*args, **kwargs)


class RoomProfile(BaseModel):
    price = models.DecimalField(
        max_digits=6,
        decimal_places=0,
        default=0
    )

    number = models.PositiveIntegerField(default=0)
    vacancy = models.PositiveIntegerField(default=0)

    room_type = models.ForeignKey(
        'listings.RoomType',
        on_delete=models.CASCADE,
        related_name='room_profiles',
        default=None
    )

    lodge = models.ForeignKey(
        Lodge,
        on_delete=models.CASCADE,
        related_name='room_profiles',
        default=None
    )

    # used for favourites
    # clients = models.ManyToManyField(
    #     Client,
    #     related_name='listings',
    # )

    # cover_image = models.ImageField(
    #     upload_to=get_upload_path_room_cover,
    #     default=default_room_cover_cdn,
    #     storage=MediaCloudinaryStorage(),
    #     null=True,
    #     blank=True,
    #     max_length=1000,
    # )

    def __str__(self):
        return f'{self.lodge} - {self.room_type}'


# class RoomImage(BaseModel, ImageOptimizationModel):
#     image = models.ImageField(
#         upload_to=get_upload_path_room,
#         default=default_room_cdn,
#         storage=MediaCloudinaryStorage(),
#         null=True,
#         blank=True,
#         max_length=1000,
#     )

#     room_profile = models.ForeignKey(
#         RoomProfile, on_delete=models.CASCADE, related_name='images'
#     )

#     class Meta(BaseModel.Meta, ImageOptimizationModel.Meta):
#         pass

#     def __str__(self):
#         return self.image.name
