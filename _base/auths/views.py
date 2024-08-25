from django.shortcuts import render

from django.urls import reverse, reverse_lazy
from django.contrib.auth.views import LogoutView
from django.contrib.auth.views import LoginView
from django.http import HttpRequest


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
        error_feedback = []
        for field, errors in form.errors.items():
            for error in errors:
                error_feedback.append(f"{error}")
        context = {
            'form': form,
            'error_feedback': error_feedback
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
