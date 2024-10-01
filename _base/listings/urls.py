from django.urls import path

from . import views as views
from .partials import home_views


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
    path(
        'lodges/<str:lodge_id>/upload-image/',
        views.upload_lodge_image,
        name='upload_lodge_image'
    ),
    path(
        'rooms/<str:room_profile_id>/upload-image/',
        views.upload_room_profile_image,
        name='upload_room_profile_image'
    ),

    path(
        'search_schools',
        home_views.search_schools,
        name='search_schools'
    ),
    path(
        'search_regions/<uuid:school_pk>/',
        home_views.search_regions,
        name='search_regions'
    ),
    path(
        'vacancy_search_result',
        views.get_vacancy_search_result,
        name='get_vacancy_search_result'
    )
]
