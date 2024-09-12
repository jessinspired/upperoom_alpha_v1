import queue
from re import T
from django.db import models
from core.models import BaseModel
from payments.models import Transaction
from listings.models import Lodge, RoomProfile, Region
from users.models import Client, Creator
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


class SubscriptionHandler(BaseModel):
    """
    Handles the subscribed listing for the associated regions
    in the subscription
    """
    THRESHOLD = 3

    verified_listings_count = models.IntegerField(default=0)

    queued_listings_count = models.IntegerField(default=0)

    is_expired = models.BooleanField(default=False)

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='subscription_handlers'
    )

    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name='subscription_handlers'
    )


class SubscribedListing(BaseModel):
    class Status(models.TextChoices):
        UNVERIFIED = 'UNVERIFIED', 'Unverified'
        VERIFIED = 'VERIFIED', 'Verified'
        PROBATION = 'PROBATION', 'Probation'
        REJECTED = 'REJECTED', 'Rejected'
        SETTLED = 'SETTLED', 'Settled'

    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.UNVERIFIED
    )

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='subscribed_listings'
    )

    room_profile = models.ForeignKey(
        RoomProfile,
        on_delete=models.CASCADE,
        related_name='subscribed_listings'
    )

    creator = models.ForeignKey(
        Creator,
        on_delete=models.CASCADE,
        related_name='client_subscribed_listings',
        default=1  # remove in production
    )

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='subscribed_listings'
    )

    subscription_handler = models.ForeignKey(
        SubscriptionHandler,
        on_delete=models.CASCADE,
        related_name='subscribed_listings',
        null=True  # change later to false
    )

    status_task_id = models.CharField(max_length=255, blank=True, null=True)
