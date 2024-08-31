from django.shortcuts import render
from listings.models import School


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
