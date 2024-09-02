from django.urls import path
import subscriptions.views as views


urlpatterns = [
    path('get_regions/', views.get_regions, name='get_regions'),
    path('order_summary/', views.get_order_summary, name='get_order_summary'),
    path(
        'subscribed_listings/<str:pk>/',
        views.get_subscribed_listings,
        name='get_subscribed_listings'
    )
]
