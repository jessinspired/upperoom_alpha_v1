from django.urls import path
import payments.views as views

urlpatterns = [
    path('order_summary/', views.get_order_summary, name='get_order_summary'),
    path(
        'initialize_transaction/',
        views.initialize_transaction,
        name='initialize_transaction'
    ),
    path('webhook/', views.webhook_view, name='webhook'),
    path('creator/transfer-info/', views.creator_transfer_info_view,
         name='creator_transfer_info'),
    path('creator/payme', views.withdraw_balance, name='pay_creator'),
]
