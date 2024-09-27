#!/usr/bin/env python3
'''listings models'''
# the 3 commented imports are for async image deleting
# import aiohttp
# import asyncio
# from decouple import config
from ast import mod
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
        related_name='subscribed_schools',
        blank=True
    )

    def __str__(self):
        return self.name


class Region(BaseModel):
    name = models.CharField(max_length=150)

    state = models.ForeignKey(
        State,
        on_delete=models.CASCADE,
        related_name='regions',
        default=None
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='regions',
        null=True,
        blank=True
    )

    subscribed_clients = models.ManyToManyField(
        Client,
        related_name='subscribed_regions',
        blank=True
    )

    def __str__(self):
        return self.name


class Landmark(BaseModel):
    name = models.CharField(max_length=150)

    region = models.ForeignKey(
        Region,
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
        related_name='subscribed_landmarks',
        blank=True
    )

    def __str__(self):
        return self.name


class LodgeGroup(BaseModel):
    name = models.CharField(
        max_length=100,
        null=False,
        blank=False
    )


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

    address = models.TextField(null=True, blank=False)

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

    region = models.ForeignKey(
        Region,
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

    group = models.ForeignKey(
        LodgeGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lodges',
        default=None
    )

    def __str__(self):
        return self.name


class LodgeImage(BaseModel):
    class Category(models.TextChoices):
        FRONT_VIEW = 'FRONT_VIEW', 'Front View'
        BACK_VIEW = 'BACK_VIEW', 'Back View'
        OTHER_VIEWS = 'OTHER_VIEWS', 'Other Views'

    lodge = models.ForeignKey(
        Lodge, related_name='lodge_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='lodges/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.OTHER_VIEWS)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"LodgeId: {self.lodge.id}, ImageId: {self.image.id}, ImageUrl: {self.image.url}" if self.image else "No Image"

    def delete(self, *args, **kwargs):
        self.image.delete(save=False)
        super().delete(*args, **kwargs)


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
        null=False
    )

    lodge = models.ForeignKey(
        Lodge,
        on_delete=models.CASCADE,
        related_name='room_profiles',
        default=None
    )

    is_vacant = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.lodge} - {self.room_type}'


class RoomProfileImage(BaseModel):
    room_profile = models.ForeignKey(
        RoomProfile, related_name='room_images', on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='rooms/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"RoomProfileId: {self.room_profile.id}, ImageId: {self.image.id}, ImageUrl: {self.image.url}" if self.image else "No Image"

    def delete(self, *args, **kwargs):
        self.image.delete(save=False)
        super().delete(*args, **kwargs)
