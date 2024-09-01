from django.http import JsonResponse, HttpResponseForbidden
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
from .utils import generate_unique_reference
from .models import Transaction


PAYSTACK_BASE_URL = 'https://api.paystack.co/transaction'


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

        if response.status_code == 200:
            json_response = response.json()

            if not json_response.get('status'):
                return HttpResponse(f'<p id="response-message">{json_response.get("message")}</p>')

            #
            if hasattr(request.user, 'transaction'):
                request.user.transaction.delete()

            Transaction.objects.create(
                amount=amount,
                reference=reference,
                client=request.user

            )

            http_response = HttpResponse(
                '<p id="response-message"></p>'
            )
            return trigger_client_event(
                http_response,
                'completeTransaction',
                {'access_code': json_response.get('data').get('access_code')}
            )
        else:
            return HttpResponse('<p id="response-message">An error occured!<br>Response not 200</p>')
    except Exception as e:
        print(e)
        return HttpResponse(f'<p id="response-message">An error occured!<br>Error<b>{e}</p>')

    return HttpResponse(f'<p id="response-message">An error occured!<br>End!</p>')


@csrf_exempt
@require_http_methods(['POST'])
def webhook_view(request):
    """
    Primary Purpose: To verify the transaction status

    - First and most preferred way to verify payments from paystack
    - Doesn't work with local host
    - Switch to this when testing on remote server with a public domain
    - web hook url is set up in paystack dashboard
    """

    # auth 1: IP Whitelisting
    # whitelist = ['52.31.139.75', '52.49.173.169', '52.214.14.220']
    # client_ip = request.META.get('REMOTE_ADDR')

    # if client_ip not in whitelist:
    #     return JsonResponse({'status': 'forbidden'}, status=400)

    # auth 2: Signature Validation
    secret = os.getenv('PAYSTACK_TEST_KEY')
    body = request.body
    payload = json.loads(body)
    print('payload :', payload)

    # handle payment success case
    if payload.get('event') == 'charge.success':
        remote_reference = payload.get('data').get('reference')
        local_reference = request.user.transaction.reference

        print(remote_reference, local_reference)

        response_amount = payload.get('data').get('amount')
        response_amount = response_amount / 100

        print(response_amount, request.user.transaction.amount)

        # confirm price

    return JsonResponse({'status': 'success'}, status=200)


def verify_payment(request, reference):
    """
    - Second way of verifying payments on paystack
    - Don't use this in production
    - Works by making a GET request to the Verify Transaction API endpoint
    from your server using your transaction reference.
    """
    pass
