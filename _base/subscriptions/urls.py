from django.urls import path
import subscriptions.views as views


urlpatterns = [
    path('get_regions/', views.get_regions, name='get_regions')
]
