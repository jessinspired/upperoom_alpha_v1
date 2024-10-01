from typing import Optional, Tuple
import os
import random
import string
from typing import List, Union
from decimal import Decimal

from django.http import JsonResponse
import requests

from subscriptions.models import SubscribedListing
from messaging.tasks import send_initial_subscribed_listings
from subscriptions.views import subscribe_for_listing
from users.models import Creator, User
from .models import CreatorTransaction, CreatorTransferInfo, Transaction

import logging

logger = logging.getLogger('payments')


def generate_unique_reference(length):
    """
    Generates a unique transaction reference.

    Args:
        length (int): The length of the reference.

    Returns:
        str: A unique transaction reference.
    """
    allowed_chars = string.ascii_letters + string.digits + '-.='

    def is_reference_unique(reference):
        """
        Checks if the reference is unique across Transaction and CreatorTransaction models.

        Args:
            reference (str): The reference to check.

        Returns:
            bool: True if unique, False otherwise.
        """
        return not (Transaction.objects.filter(reference=reference).exists() or
                    CreatorTransaction.objects.filter(reference=reference).exists())

    while True:
        reference = ''.join(random.choices(allowed_chars, k=length))

        if is_reference_unique(reference):
            return reference


def create_transfer_recipient(creator_transfer_info):
    """
    Creates a transfer recipient on Paystack and returns the recipient code.

    Args:
        creator_transfer_info (CreatorTransferInfo): An instance containing the transfer recipient details.

    Returns:
        str: The recipient code.
    """
    url = 'https://api.paystack.co/transferrecipient'
    headers = {
        'Authorization': f'Bearer {os.getenv("PAYSTACK_TEST_KEY")}',
        'Content-Type': 'application/json'
    }
    data = {
        'type': 'nuban',  # Change as needed based on the recipient's bank account type
        'name': creator_transfer_info.account_name,
        'account_number': creator_transfer_info.account_number,
        'bank_code': creator_transfer_info.bank_code,
        'currency': creator_transfer_info.currency
    }

    response = requests.post(url, headers=headers, json=data)
    response_data = response.json()

    if response_data.get('status'):
        recipient_code = response_data['data']['recipient_code']
        creator_transfer_info.recipient_code = recipient_code
        creator_transfer_info.save()
        return recipient_code
    else:
        logger.error("Failed to create transfer recipient: " +
                     response_data.get('message'))
        raise ValueError(
            "Failed to create transfer recipient: " + response_data.get('message'))


def initiate_single_transfer(recipient_code, amount, reference, reason=""):
    """
    Initiates a transfer on Paystack.

    Args:
        recipient_code (str): The recipient's code.
        amount (float): The amount to transfer (in kobo).
        reference (str): The unique reference for the transfer.
        reason (str): The reason for the transfer.

    Returns:
        dict: The response from the Paystack API.
    """
    url = 'https://api.paystack.co/transfer'
    headers = {
        'Authorization': f'Bearer {os.getenv("PAYSTACK_TEST_KEY")}',
        'Content-Type': 'application/json'
    }
    data = {
        'source': 'balance',  # Can be 'balance' or 'subaccount' depending on the source of funds
        'amount': int(amount * 100),  # Convert amount to kobo
        'reference': reference,
        'recipient': recipient_code,
        'reason': reason
    }

    response = requests.post(url, headers=headers, json=data)
    response_data = response.json()
    return response_data


def initiate_bulk_transfer(transfers: List[dict]):
    """
    Initiates a bulk transfer for multiple creators.

    Args:
        transfers (List[dict]): A list of transfer objects.
    """
    url = 'https://api.paystack.co/transfer/bulk'
    headers = {
        'Authorization': f'Bearer {os.getenv("PAYSTACK_TEST_KEY")}',
        'Content-Type': 'application/json'
    }
    data = {
        'currency': 'NGN',
        'source': 'balance',
        'transfers': transfers
    }

    response = requests.post(url, headers=headers, json=data)
    response_data = response.json()

    transactions = []

    if response_data.get('status'):
        for transfer in response_data['data']:
            transaction = CreatorTransaction.objects.create(
                recipient_code=transfer['recipient'],
                # Assuming creator_id is available
                creator=Creator.objects.get(id=transfer['creator_id']),
                # Convert from kobo to naira
                amount_transfered=transfer['amount'] / 100,
                reference=transfer['reference'],
                status=transfer['status'],
                reason=transfer['reason']
            )
            transactions.append(transaction)

        return transactions
    else:
        logger.error("Bulk transfer failed: " + response_data.get('message'))
        raise ValueError("Bulk transfer failed: " +
                         response_data.get('message'))


def handle_transfer_event(event, data):
    """
    Processes the transfer status event from Paystack.
    """
    reference = data.get('reference')
    if not reference:
        return

    try:
        # Update the transaction status based on the event type
        transaction = CreatorTransaction.objects.get(reference=reference)
        if event == 'transfer.success':
            transaction.status = 'successful'
        elif event == 'transfer.failed':
            transaction.status = 'failed'
        elif event == 'transfer.reversed':
            transaction.status = 'reversed'
        transaction.save()
    except CreatorTransaction.DoesNotExist:
        # Log or handle the case where the transaction does not exist
        pass


def handle_charge_success(data):
    """
    Handles the charge.success event from Paystack.

    Args:
        data (dict): The event data.
    """

    remote_reference = data.get('reference')
    try:
        transaction = Transaction.objects.get(reference=remote_reference)
    except Transaction.DoesNotExist:
        logger.error(
            f'Transaction not found for reference: {remote_reference}')
        return JsonResponse({'status': 'not found'}, status=404)

    transaction.paystack_id = data.get('id')

    paid_amount = data.get('amount') / 100  # Convert from kobo to naira

    if paid_amount != transaction.amount:
        logger.warning(
            f'Incomplete payment: Paid: {paid_amount}, Expected: {transaction.amount}')
        return JsonResponse({'status': 'bad request'}, status=400)

    transaction.is_fully_paid = True
    transaction.save()

    logger.info(f'Transaction fully paid: ID {transaction.pk}')
    subscription, subscribed_rooms = subscribe_for_listing(transaction)

    if subscribed_rooms.exists():
        send_initial_subscribed_listings.delay(subscription.pk)

    logger.info('Subscription for listing added')


def creator_payment_pipeline(creators: Union[Creator, List[Creator]], amount):
    """
    Handles payments for one or more creators by processing the payment pipeline.

    Args:
        creators (Union[Creator, List[Creator]]): A single Creator instance or a list of Creator instances.

    Returns:
        List[CreatorTransaction]: A list of CreatorTransaction instances representing the processed transactions.
    """
    # Ensure creators is a list
    if isinstance(creators, (Creator, User)):
        creators = [creators]

    transactions = []

    if len(creators) == 1:
        # Handle single payment
        creator = creators[0]
        if creator.transfer_profile.balance < amount:
            logger.error(
                f"Account balance is insufficient: N{creator.transfer_profile.balance}")
            raise Exception(
                f"Account balance is insufficient: N{creator.transfer_profile.balance}")
        try:
            creator_info = CreatorTransferInfo.objects.get(creator=creator)
        except CreatorTransferInfo.DoesNotExist:
            logger.error(f"No transfer info found for creator {creator.id}")
            raise ValueError(
                f"No transfer info found for creator {creator.id}")

        recipient_code = create_transfer_recipient(
            creator_info) if not creator_info.recipient_code else creator_info.recipient_code
        reference = generate_unique_reference(length=32)

        transfer_response = initiate_single_transfer(
            recipient_code=recipient_code,
            amount=amount * 100,
            reference=reference,
            reason="Payment for services"
        )

        # update creator balance
        # temporary code, not the best
        # check the status of the tranfer_response and update balance accordingly
        logger.info(
            f"Creator has been payed an amount of {amount} successfully")
        creator_info.decrement_balance(amount)

        transaction = CreatorTransaction(
            recipient_code=recipient_code,
            creator=creator,
            income=amount,
            reference=reference,
            status=transfer_response.get("status"),
            reason="Payment for services"
        )

        transaction.save()
        transactions.append(transaction)

    else:
        # Handle bulk payments
        transfers = []
        for creator in creators:
            if creator.transfer_profile.balance <= 0:
                logger.error(
                    f"Account balance is insufficient: N{creator.transfer_profile.balance} for creator with id: {creator.id}")
                raise Exception(
                    f"Account balance is insufficient: N{creator.transfer_profile.balance} for creator with id: {creator.id}")
        for creator in creators:
            try:
                creator_info = CreatorTransferInfo.objects.get(creator=creator)
            except CreatorTransferInfo.DoesNotExist:
                logger.error(
                    f"No transfer info found for creator {creator.id}")
                raise ValueError(
                    f"No transfer info found for creator {creator.id}")

            recipient_code = create_transfer_recipient(
                creator_info) if not creator.recipient_code else creator.recipient_code
            reference = generate_unique_reference(length=32)

            amount = creator_info.balance

            transfers.append({
                "amount": amount * 100,  # Assuming `balance` is in kobo
                "reference": reference,
                "reason": "Payment for services",
                "recipient": recipient_code,
                "creator_id": creator.id  # Assuming creator_id is available
            })

        if transfers:
            transfer_responses = initiate_bulk_transfer(transfers)
            transactions.extend(transfer_responses)

            for tranfer in transfers:
                creator_info: CreatorTransferInfo = Creator.objects.get(
                    id=tranfer['creator_id']).transfer_profile
                creator_info.decrement_balance(tranfer['amount'] / 100)

    return transactions


def convert_price_to_decimal(min_price: Optional[str], max_price: Optional[str]) -> Tuple[Optional[Decimal], Optional[Decimal]]:
    """
    Convert `min_price` and `max_price` from string format to `Decimal` after removing commas.

    Args:
        min_price (Optional[str]): The minimum price as a string, which may contain commas.
        max_price (Optional[str]): The maximum price as a string, which may contain commas.

    Returns:
        Tuple[Optional[Decimal], Optional[Decimal]]: The converted `min_price` and `max_price` as `Decimal` objects, or `None` if the input was empty.
    """
    if min_price:
        min_price = Decimal(min_price.replace(',', ''))
    else:
        min_price = None

    if max_price:
        max_price = Decimal(max_price.replace(',', ''))
    else:
        max_price = None

    return min_price, max_price
