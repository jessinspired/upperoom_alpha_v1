from django.contrib import admin
from .admin_models import SubscriptionAdmin
from .models import Subscription

admin.site.register(Subscription, SubscriptionAdmin)
