from django.shortcuts import render
from ..models import School
from django.db.models import Q
from django_htmx.http import trigger_client_event
from django.views.decorators.http import require_http_methods


def search_schools(request):
    query = request.GET.get('school-search-field', '')
    if not query:
        schools = School.objects.none()
        http_response = render(
            request, 'pages/home/schools-search-results.html', {'schools': schools})
        return trigger_client_event(
            http_response,
            'addSearchFieldEvents',
        )

    schools = School.objects.filter(
        Q(name__icontains=query) | Q(abbr__icontains=query)
    )

    context = {
        'schools': schools,
        'query': query
    }

    http_response = render(
        request,
        'pages/home/schools-search.html',
        context
    )

    return trigger_client_event(
        http_response,
        'addSearchFieldEvents',
        after="swap"
    )


@require_http_methods(['GET'])
def search_regions(request, school_pk):
    school = School.objects.get(pk=school_pk)

    regions = school.regions.all()
    context = {
        'regions': regions
    }

    return render(
        request,
        'pages/home/regions-search.html',
        context
    )
