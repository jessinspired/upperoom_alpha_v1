from django.urls import path
from .views import get_creator

urlpatterns = [
    path(
        'creator/',
        get_creator,
        name='get_creator'
    )
]
