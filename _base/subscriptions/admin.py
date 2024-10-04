from django.contrib import admin
from .admin_models import SubscriptionAdmin, SubscriptionHandlerAdmin
from .models import Subscription, SubscriptionHandler

admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(SubscriptionHandler, SubscriptionHandlerAdmin)
