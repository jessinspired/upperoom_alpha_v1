from django.urls import path
from .views import get_creator, get_client

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
    )
]
