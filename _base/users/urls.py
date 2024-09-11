from django.urls import path
from .views import get_creator, get_client
from . import views as views

urlpatterns = [
    path(
        'creator/',
        get_creator,
        name='get_creator'
    ),
    path(
        'client/',
        get_client,
        name='get_client'
    ),
    path(
        'client_subscriptions/',
        views.get_client_subscriptions,
        name='get_client_subscriptions'
    ),
    path(
        'creator_listings/',
        views.get_creator_listings,
        name='get_creator_listings'
    ),
    path(
        'creator_payments',
        views.get_creator_payments,
        name="get_creator_payments"
    )
]
