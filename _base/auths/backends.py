#!/usr/bin/env python3
"""Custom email based authentication backend"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    """Class for email based backend
    Args:
        ModelBackend (Class): Built in django backend class
    """

    def authenticate(self, request, username=None, password=None):
        """overloaded method to replace username with password
        Args:
            request (object): the request object
            username (string, optional): Username field. Defaults to None.
            password (string, optional): password field. Defaults to None.
        """
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None
        else:
            if user.check_password(password):
                return user
        return None
