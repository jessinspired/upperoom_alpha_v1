from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from listings.models import School


@require_http_methods('GET')
def get_home(request):

    schools = School.objects.all()
    context = {
        'schools': schools
    }

    return render(
        request,
        'home.html',
        context
    )
