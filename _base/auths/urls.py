from django.urls import path
from .views import CustomLoginView, CustomLogoutView
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
]
