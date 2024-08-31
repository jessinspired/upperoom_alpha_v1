import random
import string
from .models import Transaction


def generate_unique_reference(length):
    """
    Generates unique transaction reference

    args:
        length(int): the length of the reference
    """
    allowed_chars = string.ascii_letters + string.digits + '-.='

    while True:
        reference = ''.join(random.choices(allowed_chars, k=length))

        # Check if this reference already exists in your transaction model
        if not Transaction.objects.filter(reference=reference).exists():
            return reference
