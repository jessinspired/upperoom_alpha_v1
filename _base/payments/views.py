from decimal import Decimal
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import os
import requests
from django.http import HttpResponse
from django_htmx.http import trigger_client_event
from django.contrib import messages
from django.shortcuts import render, redirect
import json

from subscriptions.models import SubscribedListing
from .forms import CreatorTransferInfoForm, PaymentRequestForm
from auths.decorators import role_required
from listings.models import Region, RoomType
import hmac
import hashlib
from .utils import creator_payment_pipeline, generate_unique_reference, handle_charge_success, handle_transfer_event
from .models import CreatorTransferInfo, Transaction
from django.db import transaction as db_transaction
import logging
from django.urls import reverse
from listings.models import School


PAYSTACK_BASE_URL = 'https://api.paystack.co/transaction'

logger = logging.getLogger('payments')


def get_order_summary(request):
    if request.method != 'POST':
        logger.error(
            f'Error 405: Expected method for order summary is POST, but got {request.method}')
        return redirect('get_home')
    regions_pk_list = request.POST.getlist('regions')
    room_types_pk_list = request.POST.getlist('room-type')

    school_pk = request.POST.get('school')

    if not School.objects.filter(pk=school_pk).exists():
        logger.error(f'No school exists for pk {school_pk}')
        return redirect('get_home')

    if not regions_pk_list:
        logger.error(
            'Bad Request (400): No list of regions to get order summary for')

        messages.error(request, "Select at least one region")
        return redirect('get_home')

    try:
        regions = []
        for pk in regions_pk_list:
            region = Region.objects.get(pk=pk)
            regions.append(region)

        room_types = []
        if room_types_pk_list:
            for pk in room_types_pk_list:
                room_type = RoomType.objects.get(pk=pk)
                room_types.append(room_type)

        min_price = request.POST.get('min-price')
        max_price = request.POST.get('max-price')
    except:
        return redirect('get_home')

    context = {
        'regions': regions,
        'room_types': room_types,
        'amount': 1500 * len(regions),
        'school_pk': school_pk,
        'max_price': max_price,
        'min_price': min_price
    }

    return render(request, 'payments/order-summary.html', context)


@role_required(['CREATOR'])
@require_http_methods(['POST'])
def save_transfer_info(request):
    try:
        data = json.loads(request.body)
        account_number = data.get('account_number')
        bank_code = data.get('bank_code')
        currency = data.get('currency')
        bvn = data.get('bvn')

        # Validate required fields
        if not all([account_number, bank_code, currency, bvn]):
            logger.error("Missing required fields in transfer info data.")
            return JsonResponse({"error": "Missing required fields"}, status=400)

        creator = request.user

        # Create or update transfer info
        CreatorTransferInfo.objects.update_or_create(
            creator=creator,
            defaults={
                'account_number': account_number,
                'bank_code': bank_code,
                'currency': currency,
                'bvn': bvn,
            }
        )

        logger.info(
            f"Transfer info saved successfully for creator: {creator.username}")
        return JsonResponse({"message": "Transfer info saved successfully"}, status=201)

    except json.JSONDecodeError:
        logger.error("Invalid JSON data received.")
        return JsonResponse({"error": "Invalid JSON data"}, status=400)

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return JsonResponse({"error": str(e)}, status=400)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return JsonResponse({"error": "An error occurred: " + str(e)}, status=500)


@role_required(['CLIENT'], True)
@require_http_methods(['POST'])
def initialize_transaction(request):
    """
    Initializes the transaction by displaying a pop up modal
    for users to put in billing method and details
    """
    regions_pk_list = request.POST.getlist('region')
    room_types_pk_list = request.POST.getlist('room-type')
    school_pk = request.POST.get('school')
    logger.info(f'school pk {school_pk}')

    min_price = request.POST.get('min-price')
    max_price = request.POST.get('max-price')

    try:
        regions = []
        for pk in regions_pk_list:
            region = Region.objects.get(pk=pk)
            regions.append(region)

        amount = len(regions) * 1500

        school = School.objects.get(pk=school_pk)

        reference = generate_unique_reference(12)
        with db_transaction.atomic():
            existing_transaction = Transaction.objects.filter(
                reference=reference, client=request.user).first()

            if existing_transaction:
                existing_transaction.delete()

            if min_price and max_price:
                min_price = Decimal(min_price.replace(',', ''))
                max_price = Decimal(max_price.replace(',', ''))

            transaction = Transaction.objects.create(
                amount=amount,
                reference=reference,
                min_price=min_price,
                max_price=max_price,
                client=request.user,
                school=school
            )
            transaction.regions.set(regions)

            if room_types_pk_list:
                room_types = []
                for pk in room_types_pk_list:
                    room_type = RoomType.objects.get(pk=pk)
                    room_types.append(room_type)

                transaction.room_types.set(room_types)

        logger.info(
            f"Transaction initialized successfully for client: {request.user.username} - school {school.name}")
        http_response = HttpResponse(
            '<div id="global-response-message-htmx"></div>')
        params = {
            'email': request.user.email,
            'key': os.getenv('PAYSTACK_TEST_PUBLIC_KEY'),
            'amount': str(amount * 100),
            'reference': reference,
            'redirect_url': reverse('get_client_subscriptions'),
            'abort_url': reverse('abort_transaction', args=[f'{reference}'])
        }
        return trigger_client_event(
            http_response,
            'newTransaction',
            params
        )
    except Exception as e:
        logger.error(
            f"An error occurred during transaction initialization: {e}")
        context = {'messages': ['An error occured, please try again']}
        return render(request, 'elements/response-modal.html', context)


@role_required(['CLIENT'], True)
@require_http_methods(['POST'])
def abort_transaction(request, reference):
    transaction = Transaction.objects.get(reference=reference)
    transaction.delete()
    logger.info(
        f'Transaction with reference {reference} successfully deleted!')
    return HttpResponse('<div id="global-response-message-htmx"></div>')


def creator_transfer_info_view(request):
    try:
        transfer_info = CreatorTransferInfo.objects.get(creator=request.user)
    except CreatorTransferInfo.DoesNotExist:
        logger.info(
            f"No transfer info found for creator: {request.user.username}")
        transfer_info = None

    if request.method == 'POST':
        form = CreatorTransferInfoForm(request.POST, instance=transfer_info)
        if form.is_valid():
            transfer_info = form.save(commit=False)

            try:
                if transfer_info.creator is None:
                    transfer_info.creator = request.user
            except Exception as e:
                print(e)
                transfer_info.creator = request.user

            try:
                transfer_info.save()
                messages.success(
                    request, 'Transfer information saved successfully.')
                logger.info(
                    f"Transfer info updated successfully for creator: {request.user.username}")
                return redirect('get_creator_listings')
            except ValidationError as e:
                messages.error(request, str(e))
                logger.error(
                    f"Validation error during transfer info save: {e}")
    else:
        form = CreatorTransferInfoForm(instance=transfer_info)

    return render(request, 'payments/transfer-info.html', {'form': form})


@role_required(['CREATOR'])
@require_http_methods(['GET', 'POST'])
def withdraw_balance(request):
    creator = request.user
    try:
        tranfer_info = CreatorTransferInfo.objects.get(creator=creator)
    except CreatorTransferInfo.DoesNotExist:
        logger.error(
            "You have to setup a payment profile. Creator has no payment profile")
        return HttpResponse("<h1>Failed - No payment profile found. Please create one.</h1>")

    try:
        if not tranfer_info.is_validated:
            raise Exception("Payment Info is not validated")

    except Exception as e:
        logger.error("Creator payment is not validated!")
        return HttpResponse("<h1>Failed</h1>")

    if request.method == 'POST':
        form = PaymentRequestForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            try:
                creator_payment_pipeline(creator, amount)
                messages.success(
                    request, f"Payment request of N{amount} has been submitted.")
                return redirect('get_creator')
            except Exception as e:
                messages.error(request, e)

    form = PaymentRequestForm()

    return render(request, 'payments/withdraw.html', {'form': form})


@csrf_exempt
@require_http_methods(['POST'])
def webhook_view(request):
    """
    Primary Purpose: To verify the transaction status

    - Verifies payments from Paystack
    - Requires a public domain for webhooks
    - Webhook URL is set up in Paystack dashboard
    """

    # Auth 1: IP Whitelisting
    whitelist = ['52.31.139.75', '52.49.173.169', '52.214.14.220']
    client_ip = request.headers.get('X-Real-Ip')

    if client_ip not in whitelist:
        logger.warning(f'Unauthorized IP: {client_ip}')
        return JsonResponse({'status': 'forbidden'}, status=403)

    # Auth 2: Signature Validation
    secret = os.getenv('PAYSTACK_TEST_KEY')
    body = request.body
    payload = json.loads(body)
    signature = request.headers.get('X-Paystack-Signature')

    expected_signature = hmac.new(secret.encode(
        'utf-8'), body, hashlib.sha512).hexdigest()

    if signature != expected_signature:
        logger.error(f'Unauthorized signature: {signature}')
        return JsonResponse({'status': 'unauthorized'}, status=401)

    event = payload.get('event')
    data = payload.get('data', {})

    if event == 'charge.success':
        handle_charge_success(data)
        logger.info('Charge success event handled.')
    elif event in ['transfer.success', 'transfer.failed', 'transfer.reversed']:
        handle_transfer_event(event, data)
        logger.info(f'Transfer event handled: {event}')

    return JsonResponse({'status': 'success'}, status=200)
