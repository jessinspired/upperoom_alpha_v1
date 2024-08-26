#!/usr/bin/env python3
'''define services admin models'''
from django.contrib import admin
from .models import (
    Landmark,
    Area,
    School,
    RoomProfile
)


class AreaInline(admin.TabularInline):
    model = Area


class LandmarkInline(admin.TabularInline):
    model = Landmark


class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'state')
    inlines = [AreaInline, LandmarkInline]


class SchoolInline(admin.TabularInline):
    model = School


class StateAdmin(admin.ModelAdmin):
    inlines = [SchoolInline, AreaInline, LandmarkInline]


class RoomProfileInline(admin.TabularInline):
    model = RoomProfile


class LodgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'state', 'school', 'area')
    filter_horizontal = ('room_types',)
    inlines = [RoomProfileInline]


class RoomProfileAdmin(admin.ModelAdmin):
    list_display = (
        'lodge',
        'room_type',
        'price',
        'number',
        'vacancy'
    )


class LandmarkAdmin(admin.ModelAdmin):
    list_display = ('name', 'area', 'state', 'school')


class AreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'school')
    inlines = [LandmarkInline]
