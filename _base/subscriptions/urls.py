from django.urls import path
import subscriptions.views as views


urlpatterns = [
    path('get_regions/', views.get_regions, name='get_regions'),
    path(
        'subscribed_listings/<str:pk>/',
        views.get_subscribed_listings,
        name='get_subscribed_listings'
    ),
    path(
        'handle_occupied_report/<str:pk>/',
        views.handle_occupied_report,
        name='handle_occupied_report'
    )
]
