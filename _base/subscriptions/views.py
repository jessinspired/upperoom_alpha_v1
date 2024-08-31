from django.shortcuts import render, redirect
from listings.models import School, Region
from django.views.decorators.http import require_http_methods
from auths.decorators import role_required
import os
import requests
from django.http import HttpResponse
from django_htmx.http import trigger_client_event


def get_regions(request):
    school_id = request.GET.get('schools')
    school = School.objects.get(pk=school_id)

    regions = school.regions.all()
    print(regions)
    context = {
        'regions': regions
    }

    return render(
        request,
        'subscriptions/regions-partial.html',
        context
    )


def get_order_summary(request):
    # if request.method != 'POST':
    #     return redirect('get_home')
    # regions_pk_list = request.POST.getlist('regions')

    # if not regions_pk_list:
    #     return  # bad request

    # try:
    #     regions = []
    #     for pk in regions_pk_list:
    #         region = Region.objects.get(pk=pk)
    #         regions.append(region)
    # except:
    #     pass

    regions = list(School.objects.get(abbr='UNIPORT').regions.all())

    context = {
        'regions': regions,
        'amount': 1500 * len(regions)
    }

    return render(request, 'subscriptions/order-summary.html', context)


@role_required(['CLIENT'])
@require_http_methods(['POST'])
def initialize_transaction(request):
    regions_pk_list = request.POST.getlist('region')

    try:
        regions = []
        for pk in regions_pk_list:
            region = Region.objects.get(pk=pk)
            regions.append(region)

        amount = len(regions) * 1500

        url = "https://api.paystack.co/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {os.getenv('PAYSTACK_TEST_KEY')}",
            "Content-Type": "application/json"
        }
        data = {
            "email": request.user.email,
            # Paystack expects the amount in kobo, so 500000 = ₦5000
            "amount":  str(amount * 100)
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            json_response = response.json()

            if not json_response.get('status'):
                return HttpResponse(f'<p id="response-message">{json_response.get("message")}</p>')

            http_response = HttpResponse(
                '<p id="response-message"></p>'
            )
            return trigger_client_event(
                http_response,
                'completeTransaction',
                {'access_code': json_response.get('data').get('access_code')}
            )
        else:
            return HttpResponse('<p id="response-message">An error occured!<br>Please try again</p>')
    except:
        pass

    return
