from django.urls import path

import core.views as views


urlpatterns = [
    path('', views.get_home, name='get_home')
]
