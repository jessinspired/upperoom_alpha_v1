#!/usr/bin/env python3
'''define user admin models'''
from django.contrib import admin
from .models import Subscription


class LodgeInline(admin.TabularInline):
    model = Subscription.lodges.through
    extra = 1


class RoomProfileInline(admin.TabularInline):
    model = Subscription.subscribed_rooms.through
    extra = 1


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'is_expired',
        'client',
        'transaction',
    )

    inlines = [LodgeInline, RoomProfileInline]
