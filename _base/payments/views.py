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
from .forms import CreatorTransferInfoForm
from auths.decorators import role_required
from listings.models import Region
import hmac
import hashlib
from .utils import creator_payment_pipeline, generate_unique_reference, handle_charge_success, handle_transfer_event
from .models import CreatorTransferInfo, Transaction
from django.db import transaction as db_transaction
import logging

PAYSTACK_BASE_URL = 'https://api.paystack.co/transaction'

logger = logging.getLogger('payments')


def get_order_summary(request):
    if request.method != 'POST':
        from listings.models import School
        regions = list(School.objects.get(abbr='UNIPORT').regions.all())

        context = {
            'regions': regions,
            'amount': 1500 * len(regions)
        }
        logger.error(
            f'Error 405: Expected method is POST, but got {request.method}')
        return redirect('get_home')
    regions_pk_list = request.POST.getlist('regions')

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
    except:
        return redirect('get_home')

    # regions = list(School.objects.get(abbr='UNIPORT').regions.all())

    context = {
        'regions': regions,
        'amount': 1500 * len(regions)
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

    try:
        regions = []
        for pk in regions_pk_list:
            region = Region.objects.get(pk=pk)
            regions.append(region)

        amount = len(regions) * 1500

        url = f"{PAYSTACK_BASE_URL}/initialize"
        headers = {
            "Authorization": f"Bearer {os.getenv('PAYSTACK_TEST_KEY')}",
            "Content-Type": "application/json"
        }
        reference = generate_unique_reference(12)
        data = {
            "email": request.user.email,
            # Paystack expects the amount in kobo, so 500000 = ₦5000
            "amount":  str(amount * 100),
            'reference': reference
        }

        response = requests.post(url, headers=headers, json=data)
        json_response = response.json()

        if response.status_code != 200 or not json_response.get('status'):
            logger.error(
                f"Paystack initialization failed: {json_response.get('message')}")
            return HttpResponse(f'<p id="response-message">{json_response.get("message")}</p>')

        with db_transaction.atomic():
            existing_transaction = Transaction.objects.filter(
                reference=reference, client=request.user).first()

            if existing_transaction:
                existing_transaction.delete()

            transaction = Transaction.objects.create(
                amount=amount,
                reference=reference,
                client=request.user
            )
            transaction.regions.set(regions)

        logger.info(
            f"Transaction initialized successfully for client: {request.user.username}")
        # http_response = HttpResponse(
        #     '<dialog id="global-response-modal"></dialog>')
        http_response = render(request, 'elements/response-modal.html')

        return trigger_client_event(
            http_response,
            'completeTransaction',
            {'access_code': json_response.get('data').get('access_code')}
        )
    except Exception as e:
        logger.error(
            f"An error occurred during transaction initialization: {e}")
        context = {'messages': ['An error occured, please try again']}
        return render(request, 'elements/response-modal.html', context)


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
                return redirect('creator_transfer_info')
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
    try:
        tranfer_info = CreatorTransferInfo.objects.get(creator=request.user)
    except CreatorTransferInfo.DoesNotExist:
        logger.error(
            "You have to setup a payment profile. Creator has no payment profile")
        return HttpResponse("<h1>Failed</h1>")

    try:
        if not tranfer_info.is_validated:
            raise Exception("Payment Info is not validated")

    except Exception as e:
        logger.error("Creator payment is not validated!")
        return HttpResponse("<h1>Failed</h1>")

    try:
        transaction = creator_payment_pipeline(request.user, 10)
    except Exception as e:
        logger.error(e)
        return HttpResponse("<h1>Failed</h1>")

    if transaction:
        logger.info(
            f"Balance withdrawal successful for creator: {request.user.username}")
        return HttpResponse("<h1>Successful</h1>")
    logger.error(
        f"Balance withdrawal failed for creator: {request.user.username}")
    return HttpResponse("<h1>Failed</h1>")


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
