from django.db import models
from core.models import BaseModel
from payments.models import Transaction

# Create your models here.


class Subscription(BaseModel):
    transaction = models.OneToOneField(
        Transaction,
        related_name='subscription',
        null=True,
        on_delete=models.CASCADE
    )
