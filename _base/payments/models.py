from decimal import Decimal
import os
from django.db import models
from django.forms import ValidationError
import requests
from core.models import BaseModel
from django.core.validators import RegexValidator

from users.models import Client, Creator
from listings.models import Region


BASE_FARE = Decimal('50.00')


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


class CreatorTransferInfo(BaseModel):
    """
    A Django model that stores transfer-related information for a creator.

    Attributes:
        creator (OneToOneField): A one-to-one relationship with the Creator model.
        account_number (CharField): The bank account number of the creator, validated to be between 10 and 15 digits.
        bank_code (CharField): The bank code for the creator's bank, validated to be between 3 and 10 digits.
        account_name (CharField): The resolved name of the account holder. Optional.
        bvn (CharField): The Bank Verification Number of the creator, validated to be exactly 11 digits.
        currency (CharField): The currency in which transfers are made. Currently supports 'NGN' for Nigerian Naira.
        balance (DecimalField): The balance of the creator's account, with a default value of 0.00.

    Methods:
        save: Override the default save method to include validation and account resolution with Paystack before saving the instance.
    """

    creator = models.OneToOneField(
        Creator,
        related_name='transfer_profile',
        on_delete=models.CASCADE
    )

    account_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(
            regex=r'^\d{10,15}$', message='Invalid account number')]
    )

    bank_code = models.CharField(
        max_length=10,
        validators=[RegexValidator(
            regex=r'^\d{3,10}$', message='Invalid bank code')]
    )

    account_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="The resolved name of the account holder"
    )

    bvn = models.CharField(
        max_length=11,
        validators=[RegexValidator(regex=r'^\d{11}$', message='Invalid BVN')],
        help_text="The customer's BVN (Bank Verification Number)"
    )

    currency = models.CharField(
        max_length=5,
        choices=[('NGN', 'Nigerian Naira')],
    )

    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )

    is_validated = models.BooleanField(
        default=False,
    )

    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )

    recipient_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="A unique code identifying the recipient. This code should be used to refer to the recipient in transactions."
    )

    is_validated = models.BooleanField(
        default=False,
    )

    def increment_balance(self):
        """Increment the balance by a given amount."""
        self.balance += BASE_FARE
        self.save()

    def decrement_balance(self, amount):
        """Decrement the balance by a given amount."""
        amount = Decimal(amount)
        if amount < Decimal('0.00'):
            raise ValidationError("Amount must be non-negative.")
        if self.balance - amount < Decimal('0.00'):
            raise ValidationError("Balance cannot be negative.")
        self.balance -= amount
        self.save()

    def save(self, *args, **kwargs):
        """Override the save method to perform additional validations and resolve account details before saving the record."""
        # Step 1: Resolve account details from Paystack
        resolve_url = f'https://api.paystack.co/bank/resolve?account_number={self.account_number}&bank_code={self.bank_code}'
        headers = {
            'Authorization': f'Bearer {os.getenv("PAYSTACK_TEST_KEY")}'
        }

        resolve_response = requests.get(resolve_url, headers=headers)
        resolve_data = resolve_response.json()

        if resolve_data.get("status"):
            self.account_name = resolve_data['data']['account_name']
        else:
            raise ValidationError(
                "Failed to resolve account details. Please check the account number and bank code.")

        if not self.is_validated:
            # Step 2: Verify creator name with BVN and bank account using Paystack
            creator_first_name = self.creator.first_name
            creator_last_name = self.creator.last_name

            verification_url = f'https://api.paystack.co/customer/{self.creator.customer_code}/identification'
            verification_data = {
                "country": "NG",
                "type": "bank_account",
                "account_number": self.account_number,
                "bvn": self.bvn,
                "bank_code": self.bank_code,
                "first_name": creator_first_name,
                "last_name": creator_last_name
            }

            verification_response = requests.post(
                verification_url, headers=headers, json=verification_data)
            verification_result = verification_response.json()

            if not verification_result.get("status"):
                if verification_result.get("message") != "Customer already validated using the same credentials":
                    raise ValidationError(
                        "Failed to verify account details. The name on the bank account does not match the creator's name.")

            self.is_validated = True

        super().save(*args, **kwargs)
        """
        Override the save method to perform additional validations and resolve account details before saving the record.

        Steps performed:
            1. Resolve account details from Paystack using the provided account number and bank code.
            2. Verify that the resolved account name matches the creator's name and the BVN is correct.
            3. Save the record if all checks pass.

        Raises:
            ValidationError: If account details cannot be resolved or if the creator's name does not match the bank account.
        """
        # Step 1: Resolve account details from Paystack
        resolve_url = f'https://api.paystack.co/bank/resolve?account_number={self.account_number}&bank_code={self.bank_code}'
        headers = {
            'Authorization': f'Bearer {os.getenv("PAYSTACK_TEST_KEY")}'
        }

        resolve_response = requests.get(resolve_url, headers=headers)
        resolve_data = resolve_response.json()

        # Check if the account resolution API call was successful
        if resolve_data.get("status"):
            self.account_name = resolve_data['data']['account_name']
        else:
            raise ValidationError(
                "Failed to resolve account details. Please check the account number and bank code.")

        if not self.is_validated:
            # Step 2: Verify creator name with BVN and bank account using Paystack
            creator_first_name = self.creator.first_name
            creator_last_name = self.creator.last_name

            verification_url = f'https://api.paystack.co/customer/{self.creator.customer_code}/identification'
            verification_data = {
                "country": "NG",
                "type": "bank_account",
                "account_number": self.account_number,
                "bvn": self.bvn,
                "bank_code": self.bank_code,
                "first_name": creator_first_name,
                "last_name": creator_last_name
            }

            verification_response = requests.post(
                verification_url, headers=headers, json=verification_data)
            verification_result = verification_response.json()
            print(verification_result)
            if not verification_result.get("status"):
                if verification_result.get("message") == "Customer already validated using the same credentials":
                    pass
                else:
                    raise ValidationError(
                        "Failed to verify account details. The name on the bank account does not match the creator's name.")

            self.is_validated = True

        # Save the record if all checks pass
        super().save(*args, **kwargs)


class CreatorTransaction(BaseModel):
    """
    Model representing a transaction made for the creator.

    Attributes:
    - recipient_code: A unique code identifying the recipient. This is used to refer to the recipient in transactions.
    - creator: A foreign key linking to the Creator model. This denotes the creator who the transaction is meant for.
    - amount_transferred: The amount of money transferred in the transaction.
    - reference: A unique reference code for tracking the transaction. It helps in managing and reconciling transactions.
    - status: The status of the transaction (e.g., 'pending', 'successful', 'failed'). Indicates the current state of the transaction.
    - reason: The reason for the transfer. Provides context or explanation for why the transaction was made.
    """

    recipient_code = models.CharField(
        max_length=50,
        help_text="A unique code identifying the recipient. This code should be used to refer to the recipient in transactions."
    )

    creator = models.ForeignKey(
        Creator,
        on_delete=models.CASCADE,
        related_name='creator_transactions',
        help_text="The creator who initiated the transaction. This establishes a one-to-many relationship with the Creator model."
    )

    income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The amount of money transferred in the transaction."
    )

    reference = models.CharField(
        max_length=100,
        unique=True,
        help_text="A unique reference code for tracking the transaction. Helps in managing and reconciling transactions."
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('successful', 'Successful'),
            ('failed', 'Failed'),
            ('reversed', 'Reversed')
        ],
        default='pending',
        help_text="The current status of the transaction."
    )

    reason = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="The reason for the transfer. Provides context or explanation for why the transaction was made."
    )
