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
import logging
from django_htmx.http import HttpResponseClientRefresh


UserModel = get_user_model()
BACKEND = 'auths.backends.EmailBackend'

logger = logging.getLogger('auths')


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
        logger.error('400 Bad Request Role not found in creator and client')
        messages.error(request, 'Please select a role')
        return HttpResponseClientRefresh()

    if not form.is_valid():
        logger.error(f'Init email auth error: {form.errors.items()}')
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{error}')
        return HttpResponseClientRefresh()

    email = form.cleaned_data.get('email')
    user = User.objects.filter(email=email)

    # check if email exists locally
    if user:
        messages.error(request, 'This email ID is already registered')
        return HttpResponseClientRefresh()

    token_obj = EmailVerificationToken.objects.filter(email=email)
    if token_obj:
        token_obj.delete()

    # Generate and save the verification token
    token = EmailVerificationToken.create_token(email, role)

    uuid = token.uuid_code
    send_verification_mail.delay(email, uuid)

    home_url = os.getenv('HOME_URL')
    url = f"{home_url}/auth/verify_email/{uuid}/"
    logger.info(f'Email verification link for {email}: {url}')

    context = {

        'messages': ['Click the link sent to your email to get verfied!']
    }

    return render(request, 'elements/response-modal.html', context)


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
        return redirect('init_email_auth')


@require_http_methods(['POST'])
def finish_email_auth(request):
    role = None
    form = None

    modified_post_data = request.POST.copy()
    modified_post_data['password2'] = modified_post_data.get('password1')

    email = modified_post_data.get('email')

    if not email:
        messages.error(request, 'No email provided')
        return redirect('init_email_auth')

    try:
        email_verification_obj = EmailVerificationToken.objects.get(
            email=email)
    except EmailVerificationToken.DoesNotExist as e:
        logger.error(f'finish email auth error for email: {email}\n {e}')
        messages.error(request, "Your email address must be verified.")
        return redirect('init_email_auth')

    if not email_verification_obj.is_verified:
        messages.error(request, "Your email address must be verified.")
        return redirect('init_email_auth')

    role = email_verification_obj.role
    if not role:
        email_verification_obj.delete()
        messages.error(request, 'No role provided')
        return redirect('init_email_auth')

    if role == 'CREATOR':
        form = CreatorRegistrationForm(modified_post_data)
    elif role == 'CLIENT':
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
        # email = form.cleaned_data.get('email')

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

        if role == 'CREATOR':
            profile = CreatorProfile.objects.get(user=user)
        elif role == 'CLIENT':
            profile = ClientProfile.objects.get(user=user)

        profile.phone_number = form.cleaned_data.get('phone_number')
        profile.save()

        login(request, user, BACKEND)

        logger.info(f'{role} account creation complete for {email}')

        if role == 'CREATOR':
            return redirect('get_creator')
        elif role == 'CLIENT':
            return redirect('get_client')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{error}')

        return redirect('verify_email', uuid_code=email_verification_obj.uuid_code)


class CustomLoginView(LoginView):
    """Used to render either full or partial html with htmx"""

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        # Store the request in an instance variable to use it later in get_template_names
        self.request = request
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        logger.error(f'Login error: {form.errors.items()}')
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')

        return redirect('login')

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
