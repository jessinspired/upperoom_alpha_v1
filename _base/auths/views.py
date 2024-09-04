from django.shortcuts import render, redirect

from django.urls import reverse, reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpRequest, HttpResponse
from .forms import (
    EmailVerificationForm,
    ClientRegistrationForm,
    CreatorRegistrationForm
)
from django.contrib.auth import get_user_model, login, logout
from users.models import User, CreatorProfile, ClientProfile
from messaging.tasks import send_verification_mail
from .models import EmailVerificationToken
from django.views.decorators.http import require_http_methods
from django.contrib import messages
import os


UserModel = get_user_model()
BACKEND = 'auths.backends.EmailBackend'


def init_email_auth(request):
    if request.method != 'POST':
        form = EmailVerificationForm()
        context = {
            'form': form
        }
        return render(request, 'auths/verify-email.html', context)

    form = EmailVerificationForm(request.POST)
    role = request.POST.get('role')

    if role not in ['CREATOR', 'CLIENT']:
        return render(request, 'core/error_pages/400.html', status=400)

    if not form.is_valid():
        error_list = []
        for field, errors in form.errors.items():
            for error in errors:
                error_list.append(f"{error}")
        context = {
            'form': form,
            'error_list': error_list
        }
        return render(
            request,
            'auths/verify-email.html',
            context
        )

    email = form.cleaned_data.get('email')
    user = User.objects.filter(email=email)

    # check if email exists locally
    if user:
        context = {
            'form': form,
            'error_list': ['This email ID is already registered']
        }
        return render(
            request,
            'auths/verify-email.html',
            context
        )

    token_obj = EmailVerificationToken.objects.filter(email=email)
    if token_obj:
        token_obj.delete()

    # Generate and save the verification token
    token = EmailVerificationToken.create_token(email, role)

    uuid = token.uuid_code
    send_verification_mail.delay(email, uuid)

    # home_url = os.getenv('HOME_URL', 'http://127.0.0.1:8000')
    # url = f"{home_url}/auth/verify_email/{uuid}"
    # return HttpResponse(f'<a href="{url}">Click link</a>')

    return HttpResponse(f'<p>Click the link sent to your mail for verification</p>')


@require_http_methods(['GET'])
def verify_email(request, uuid_code):
    if EmailVerificationToken.is_valid_token(uuid_code):
        token = EmailVerificationToken.objects.get(uuid_code=uuid_code)
        token.is_verified = True
        token.save()
        role, form = None, None

        if token.role == 'CLIENT':
            form = ClientRegistrationForm(initial={
                'email': token.email
            })
            role = 'client'
        elif token.role == 'CREATOR':
            form = CreatorRegistrationForm(initial={
                'email': token.email
            })
            role = 'creator'

        context = {
            'form': form,
            'role': role
        }

        return render(
            request,
            'auths/register.html',
            context
        )
    else:
        form = EmailVerificationForm()

        messages.error(
            request, 'Verification status is invalid or has expired. Try again')
        return render(request, 'auths/register.html', {'form': form})


@require_http_methods(['POST', 'GET'])
def finish_email_auth(request):
    role = request.GET.get('role')
    form = None
    if role not in ['creator', 'client']:
        return render(request, 'error_pages/400-bad-request.html', status=400)

    if request.method == 'POST':
        modified_post_data = request.POST.copy()
        modified_post_data['password2'] = modified_post_data.get('password1')
        if role == 'creator':
            form = CreatorRegistrationForm(modified_post_data)
        elif role == 'client':
            form = ClientRegistrationForm(modified_post_data)

        if form.is_valid():
            user = form.save(commit=False)
            if not user:
                messages.error(
                    request, "Encountered an error while creating Account.")
                return redirect('init_email_auth')
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            phone = form.cleaned_data.get('phone_number')
            email = form.cleaned_data.get('email')

            token = EmailVerificationToken.objects.get(email=email)
            if not token.is_verified:
                messages.error("Your email address must be verified.")
                return redirect('init_email_auth')

            import random
            while True:
                random_number = str(random.randint(1000000, 9999999))
                username = f'{first_name}{last_name}{random_number}'

                if not UserModel.objects.filter(username=username):
                    user.username = username
                    user.authentication_means = 'EMAIL'
                    user = form.save()
                    break

            if role == 'creator':
                profile = CreatorProfile.objects.get(user=user)
            elif role == 'client':
                profile = ClientProfile.objects.get(user=user)

            profile.phone_number = form.cleaned_data.get('phone_number')
            profile.save()

            login(request, user, BACKEND)

            if role == 'creator':
                return redirect('get_creator')
            elif role == 'client':
                return redirect('get_client')
        else:
            error_feedback = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_feedback.append(f"{error}")
            context = {
                'form': form,
                'error_feedback': error_feedback,
                'role': role
            }
            return render(
                request,
                'auths/register.html',
                context
            )
    else:
        if role == 'creator':
            form = CreatorRegistrationForm()
        elif role == 'client':
            form = ClientRegistrationForm()

        return render(request, 'auths/register.html', {'form': form})


class CustomLoginView(LoginView):
    """Used to render either full or partial html with htmx"""

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        # Store the request in an instance variable to use it later in get_template_names
        self.request = request
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        error_list = []
        for field, errors in form.errors.items():
            for error in errors:
                error_list.append(f"{error}")
        context = {
            'form': form,
            'error_list': error_list
        }

        return render(
            self.request,
            'auths/login.html',
            context
        )

    def get_success_url(self):
        """
        Returns the URL to redirect to after login.
        Redirects based on the user's role.
        """
        if self.request.user.role == 'CREATOR':
            return reverse_lazy('get_creator')
        elif self.request.user.role == 'CLIENT':
            return reverse_lazy('get_client')


class CustomLogoutView(LogoutView):
    def get_next_page(self):
        # Construct the redirect URL with query parameter
        base_url = reverse_lazy('login').url
        return f'{base_url}?is_fragment=true'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add your additional context data here
        # context['form'] = EmailBasedLoginForm()
        return context
