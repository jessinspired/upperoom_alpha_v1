from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods('GET')
def get_home(request):

    return render(
        request,
        'home.html',
    )
