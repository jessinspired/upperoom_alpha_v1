#!/usr/bin/env python3
'''define user admin models'''
from django.contrib import admin
from .models import Transaction


class RoomProfileInline(admin.TabularInline):
    model = Transaction.regions.through
    extra = 1


class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'amount',
        'reference',
        'client',
        'paystack_id',
        'is_fully_paid'
    )

    inlines = [RoomProfileInline]
