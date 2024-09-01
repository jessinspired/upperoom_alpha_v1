from django.db import models
from core.models import BaseModel
from users.models import Client


class Transaction(BaseModel):
    """
    Holds record of current transaction for vacancy
    subscription before payment is confirmed
    """
    amount = models.CharField(max_length=20, null=False)
    reference = models.CharField(max_length=50, null=False)

    client = models.OneToOneField(
        Client,
        on_delete=models.CASCADE,
        related_name='transaction',
        default=None
    )
