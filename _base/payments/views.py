from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import os
import requests
from django.http import HttpResponse
from django_htmx.http import trigger_client_event
import json
from auths.decorators import role_required
from listings.models import Region
import hmac
import hashlib
from .utils import generate_unique_reference, handle_charge_success, handle_transfer_event
from .models import CreatorTransferInfo, Transaction
from django.db import transaction as db_transaction
import logging

PAYSTACK_BASE_URL = 'https://api.paystack.co/transaction'

logger = logging.getLogger('payments')


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
            return JsonResponse({"error": "Missing required fields"}, status=400)
        
        creator = request.user
        
        # Create or update transfer info
        try:
            CreatorTransferInfo.objects.update_or_create(
                creator=creator,
                defaults={
                    'account_number': account_number,
                    'bank_code': bank_code,
                    'currency': currency,
                    'bvn': bvn,
                }
            )
            
            return JsonResponse({"message": "Transfer info saved successfully"}, status=201)
        
        except ValidationError as e:
            # Handle validation errors (e.g., account resolving, name mismatch)
            return JsonResponse({"error": str(e)}, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    
    except Exception as e:
        return JsonResponse({"error": "An error occurred: " + str(e)}, status=500)

@role_required(['CLIENT'])
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

        if response.status_code != 200:
            return HttpResponse('<p id="response-message">An error occured!<br>Response not 200</p>')

        json_response = response.json()
        if not json_response.get('status'):
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

        http_response = HttpResponse(
            '<p id="response-message"></p>'
        )
        return trigger_client_event(
            http_response,
            'completeTransaction',
            {'access_code': json_response.get('data').get('access_code')}
        )
    except Exception as e:
        print(e)
        return HttpResponse(f'<p id="response-message">An error occured!<br>Error<b>{e}</p>')


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

    expected_signature = hmac.new(secret.encode('utf-8'), body, hashlib.sha512).hexdigest()

    if signature != expected_signature:
        logger.error(f'Unauthorized signature: {signature}')
        return JsonResponse({'status': 'unauthorized'}, status=401)

    event = payload.get('event')
    data = payload.get('data', {})

    if event == 'charge.success':
        handle_charge_success(data)
    elif event in ['transfer.success', 'transfer.failed', 'transfer.reversed']:
        handle_transfer_event(event, data)

    return JsonResponse({'status': 'success'}, status=200)