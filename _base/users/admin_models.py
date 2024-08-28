#!/usr/bin/env python3
'''define user admin models'''
from django.contrib import admin
from listings.models import Lodge
from .models import CreatorProfile, ClientProfile


class LodgeInline(admin.TabularInline):
    model = Lodge


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name',
                    'last_name')


class CreatorProfileInline(admin.TabularInline):
    model = CreatorProfile


class CreatorAdmin(admin.ModelAdmin):
    '''adds Creator details to admin panel
    Args:
        admin (ModelAdmin): built-in django Admin model
    '''
    list_display = ('username', 'email', 'first_name',
                    'last_name')

    inlines = [LodgeInline, CreatorProfileInline]


class ClientProfileInline(admin.TabularInline):
    model = ClientProfile


class ClientAdmin(admin.ModelAdmin):
    '''adds Client details to admin panel
    Args:
        admin (ModelAdmin): built-in django Admin model
    '''
    list_display = ('username', 'email', 'first_name',
                    'last_name')

    inlines = [ClientProfileInline]
