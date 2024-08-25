from django.urls import path
from .views import (
    CustomLoginView,
    CustomLogoutView,
    initiate_email_verification,
    verify_email
)
from .forms import EmailBasedLoginForm

urlpatterns = [
    path(
        'login/',
        CustomLoginView.as_view(
            authentication_form=EmailBasedLoginForm,
            template_name='auths/login.html'
        ),
        name='login'
    ),
    path(
        'logout/',
        CustomLogoutView.as_view(
            template_name='auths/login.html'),
        name='logout'
    ),
    path(
        'initiate_email_verification/',
        initiate_email_verification,
        name='initiate_email_verification'
    ),
    path(
        'verify_email/<str:uuid_code>',
        verify_email,
        name='verify_email'
    ),
]
