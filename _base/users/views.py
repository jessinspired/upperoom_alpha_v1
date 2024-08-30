from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

# Create your views here.


@login_required
def get_creator(request):
    return render(request, 'users/creator.html')


@login_required
def get_client(request):
    return render(request, 'users/client.html')
