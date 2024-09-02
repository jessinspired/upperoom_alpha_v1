from django.db import models
from core.models import BaseModel
from payments.models import Transaction
from listings.models import Lodge, RoomProfile


class Subscription(BaseModel):
    transaction = models.OneToOneField(
        Transaction,
        related_name='subscription',
        null=True,
        on_delete=models.CASCADE
    )

    lodges = models.ManyToManyField(
        Lodge,
        related_name='subscriptions'
    )

    subscribed_rooms = models.ManyToManyField(
        RoomProfile,
        related_name='subscriptions'
    )
