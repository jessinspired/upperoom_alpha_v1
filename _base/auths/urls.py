from django.urls import path
from .views import (
    CustomLoginView,
    CustomLogoutView,
    init_email_auth,
    verify_email,
    finish_email_auth
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
        'init_email_auth/',
        init_email_auth,
        name='init_email_auth'
    ),
    path(
        'verify_email/<str:uuid_code>',
        verify_email,
        name='verify_email'
    ),
    path(
        'finish_email_auth/',
        finish_email_auth,
        name='finish_email_auth'
    )
]
