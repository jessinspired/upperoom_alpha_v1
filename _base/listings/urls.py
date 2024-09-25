from django.urls import path

from . import views as views


urlpatterns = [
    path('register_lodge/', views.register_lodge, name='register_lodge'),
    path(
        'lodge_profile/<str:pk>/',
        views.get_lodge_profile,
        name='get_lodge_profile'
    ),
    path(
        'update_room_profile/<str:pk>',
        views.update_room_profile,
        name='update_room_profile'
    ),
    path(
        'get_schools',
        views.get_schools,
        name='get_schools'
    ),
    path(
        'get_regions_select',
        views.get_regions_select,
        name='get_regions_select'
    ),
    path(
        'get_landmarks_select',
        views.get_landmarks_select,
        name='get_landmarks_select'
    ),
]
