from django.contrib import admin
from .admin_models import TransactionAdmin
from .models import Transaction

admin.site.register(Transaction, TransactionAdmin)
