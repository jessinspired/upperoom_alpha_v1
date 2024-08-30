from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from auths.decorators import role_required

# Create your views here.


@login_required
@role_required(['CREATOR'])
def get_creator(request):
    return render(request, 'users/creator.html')


@login_required
@role_required(['CLIENT'])
def get_client(request):
    return render(request, 'users/client.html')
