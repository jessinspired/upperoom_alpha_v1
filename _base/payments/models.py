from django.db import models
from core.models import BaseModel


class Transaction(BaseModel):
    amount = models.CharField(max_length=20, null=False)
    reference = models.CharField(max_length=50, null=False)
