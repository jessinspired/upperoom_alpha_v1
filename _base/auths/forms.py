#!/usr/bin/env python3

from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm
)

from users.models import Client, Creator


class EmailBasedLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(
            attrs={
                'autofocus': True,
                'placeholder': 'Email'
            }))
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Password'
            }
        )
    )


class EmailVerificationForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(
            attrs={
                'autofocus': True,
                'placeholder': 'Email'
            }))


class ClientRegistrationForm(UserCreationForm):
    '''Defines form for customer Creation
    Args:
        UserCreationForm (form): built in django class for user creation
        - This form inherits from it
    Returns:
        user (customer) object: Returns the created customer object on save
    '''
    email = forms.EmailField(
        label='Email',
        widget=forms.TextInput(attrs={
            'readonly': 'readonly',
            'placeholder': 'Email'
        })
    )

    phone_number = forms.CharField(
        label='Phone Number',
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Phone number'
        })
    )

    password1 = forms.CharField(
        label='Password',
        help_text='',
        required=True,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password'
        })
    )

    password2 = forms.CharField(
        label='Confirm Password',
        help_text='',
        required=True,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm your password'
        })
    )

    first_name = forms.CharField(
        label='First Name',
        help_text='',
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'First name'
        })
    )

    last_name = forms.CharField(
        label='Last Name',
        help_text='',
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Last name'
        })
    )

    class Meta:
        '''defines meta data for form
        - model: assigns associated proxy model
                (i.e extends User model), customer
        - fields: rendered fields on form in web page
        '''
        model = Client
        fields = [
            'email',
            'first_name',
            'last_name',
            'password1',

        ]

    def save(self, commit=True):
        '''assigns role to user (customer) and saves to database
        Args:
            commit (bool, optional): saves user to db. Defaults to True.
        Returns:
            created user: customer object
        '''
        user = super().save(commit=False)
        user.role = "CLIENT"
        # user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user


class CreatorRegistrationForm(UserCreationForm):
    '''Defines form for customer Creation
    Args:
        UserCreationForm (form): built in django class for user creation
        - This form inherits from it
    Returns:
        user (customer) object: Returns the created customer object on save
    '''
    email = forms.EmailField(
        label='Email',
        widget=forms.TextInput(attrs={
            'readonly': 'readonly',
            'placeholder': 'Email'
        })
    )

    phone_number = forms.CharField(
        label='Phone Number',
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Phone number'
        })
    )

    password1 = forms.CharField(
        label='Password',
        help_text='',
        required=True,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password'
        })
    )

    password2 = forms.CharField(
        label='Confirm Password',
        help_text='',
        required=True,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm your password'
        })
    )

    first_name = forms.CharField(
        label='First Name',
        help_text='',
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'First name'
        })
    )

    last_name = forms.CharField(
        label='Last Name',
        help_text='',
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Last name'
        })
    )

    class Meta:
        '''defines meta data for form
        - model: assigns associated proxy model
                (i.e extends User model), Creator
        - fields: rendered fields on form in web page
        '''
        model = Creator
        fields = [
            'email',
            'first_name',
            'last_name',
            'password1',
        ]

    def save(self, commit=True):
        '''assigns role to user (creator) and saves to database
        Args:
            commit (bool, optional): saves user to db. Defaults to True.
        Returns:
            created user: creator object
        '''
        user = super().save(commit=False)
        user.role = "CREATOR"
        if commit:
            user.save()
        return user


# class RoleAssignmentForm(forms.Form):
#     # Exclude DEFAULT and RIDER roles
#     ROLE_CHOICES = [
#         (role, label) for role, label in User.Role.choices
#         if role not in {User.Role.DEFAULT, User.Role.RIDER}
#     ]

#     role = forms.ChoiceField(
#         choices=ROLE_CHOICES,
#         widget=forms.Select(attrs={'class': 'form-control'}),
#         required=True,
#         label="Assign Role"
#     )


# class CustomPasswordResetForm(PasswordResetForm):
#     email = forms.EmailField(
#         label='Enter email associated with your account', max_length=254)


# class CustomSetPasswordForm(SetPasswordForm):
#     new_password1 = forms.CharField(
#         label='New password', widget=forms.PasswordInput)
#     new_password2 = forms.CharField(
#         label='Confirm new password', widget=forms.PasswordInput)
