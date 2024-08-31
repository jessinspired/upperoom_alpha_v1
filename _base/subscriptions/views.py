from django.shortcuts import render, redirect
from listings.models import School, Region
from django.views.decorators.http import require_http_methods


@require_http_methods(['GET'])
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
