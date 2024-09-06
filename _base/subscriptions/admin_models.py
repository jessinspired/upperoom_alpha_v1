#!/usr/bin/env python3
'''define user admin models'''
from django.contrib import admin
from .models import Subscription, SubscribedListing


@admin.register(SubscribedListing)
class SubscribedListingAdmin(admin.ModelAdmin):
    list_display = ('status', 'subscription', 'room_profile',
                    'creator', 'client', 'created_at', 'updated_at')
    list_filter = ('status', 'creator', 'client')
    search_fields = ('room_profile__name', 'creator__name', 'client__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    def room_profile_name(self, obj):
        return obj.room_profile.room_type.get_name_display()

    def client_name(self, obj):
        return obj.client.name


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
