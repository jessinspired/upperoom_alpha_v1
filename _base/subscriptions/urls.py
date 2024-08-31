from django.urls import path
import subscriptions.views as views


urlpatterns = [
    path('get_regions/', views.get_regions, name='get_regions'),
    path('order_summary/', views.get_order_summary, name='get_order_summary'),
    path(
        'initialize_transaction/',
        views.initialize_transaction,
        name='initialize_transaction'
    )
]
