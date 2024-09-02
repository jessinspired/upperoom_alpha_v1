from django.db import models
from core.models import BaseModel
from users.models import Client
from listings.models import Region


class Transaction(BaseModel):
    """
    Keeps track of transaction
    Associates transaction with subscription
    """
    amount = models.DecimalField(
        max_digits=10,
        null=False,
        decimal_places=2
    )
    reference = models.CharField(max_length=50, null=False)

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='transactions',
        default=None
    )

    paystack_id = models.IntegerField(
        null=True,
        default=None,
    )

    regions = models.ManyToManyField(
        Region,
        related_name='transactions'
    )

    is_fully_paid = models.BooleanField(
        null=False,
        default=False
    )
