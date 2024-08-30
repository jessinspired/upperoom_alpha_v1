#!/usr/bin/env python3
'''define services admin models'''
from django.contrib import admin
from .models import (
    Landmark,
    Region,
    School,
    RoomProfile
)


class RegionInline(admin.TabularInline):
    model = Region


class LandmarkInline(admin.TabularInline):
    model = Landmark


class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'state')
    inlines = [RegionInline, LandmarkInline]


class SchoolInline(admin.TabularInline):
    model = School


class StateAdmin(admin.ModelAdmin):
    inlines = [SchoolInline, RegionInline, LandmarkInline]


class RoomProfileInline(admin.TabularInline):
    model = RoomProfile


class LodgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'state', 'school', 'region')
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
    list_display = ('name', 'region', 'state', 'school')


class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'school')
    inlines = [LandmarkInline]
