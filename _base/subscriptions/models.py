from django.db import models
from core.models import BaseModel
from payments.models import Transaction
from listings.models import Lodge, RoomProfile
from users.models import Client
from django.core.validators import MaxValueValidator


class Subscription(BaseModel):
    is_expired = models.BooleanField(null=False, default=False)

    number_of_listings_sent = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(20)]
    )

    client = models.ForeignKey(
        Client,
        related_name='subscriptions',
        on_delete=models.CASCADE,
        default=None
    )

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
