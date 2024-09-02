from django.urls import path
import payments.views as views

urlpatterns = [
    path(
        'initialize_transaction/',
        views.initialize_transaction,
        name='initialize_transaction'
    ),
    path('webhook/', views.webhook_view, name='webhook'),

]
