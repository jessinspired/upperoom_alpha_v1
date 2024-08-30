from django.shortcuts import render

from django.urls import reverse, reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpRequest, HttpResponse
from .forms import (
    EmailVerificationForm,
    ClientRegistrationForm,
    CreatorRegistrationForm
)
from django.contrib.auth import get_user_model, login, logout
from users.models import User
from messaging.tasks import send_email_verification_mail
from .models import EmailVerificationToken
from django.views.decorators.http import require_http_methods
from django.contrib import messages


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

    send_email_verification_mail(email, token.uuid_code)

    return HttpResponse('<p>Check Mail</p>')


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
        if request.GET.get('is_fragment', None):
            return render(request, 'auths/html_fragments/register-customer-fragment.html', {'form': form})
        return render(request, 'auths/register_customer.html', {'form': form})


class CustomLoginView(LoginView):
    """Used to render either full or partial html with htmx"""

    # def get_template_names(self):
    #     template_name = super().get_template_names()
    #     if self.request.GET.get('is_fragment') == 'true':
    #         return ['auths/html_fragments/login-fragment.html']
    #     else:
    #         return ['auths/login.html']

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
            'auths/html_fragments/login-fragment.html',
            context
        )

    def get_success_url(self):
        """
        Returns the URL to redirect to after login.
        Redirects based on the user's role.
        """
        if self.request.user.role == 'CUSTOMER':
            return reverse_lazy('get_customer_dashboard_fragment')
        elif self.request.user.role == 'BUSINESS':
            return reverse_lazy('get_business_dashboard_fragment')


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
