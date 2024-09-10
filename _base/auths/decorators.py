#!/usr/bin/env python3
"""Decorators for users views"""
from django.shortcuts import render, redirect
from functools import wraps
from django.contrib import messages
import logging
from django_htmx.http import HttpResponseClientRefresh

logger = logging.getLogger('auths')


def role_required(required_roles, trigger_reload=False):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                roles_str = ', '.join([role.lower()
                                      for role in required_roles])
                messages.error(request,
                               f'Login as a {roles_str} to access this resource')
                logger.error(
                    f'User not authenticated, expected role: {required_roles}')

                if trigger_reload and request.htmx:
                    return HttpResponseClientRefresh()
                return redirect('init_email_auth')

            VALID_ROLES = {'CREATOR', 'CLIENT'}

            if isinstance(required_roles, str):
                required_roles_list = [required_roles]
            elif isinstance(required_roles, list):
                required_roles_list = required_roles
            else:
                return render(request, 'error_pages/400.html', status=400)

            # Validate required_roles
            if not all(role in VALID_ROLES for role in required_roles_list):
                messages.error(request,
                               f'Unexpected roles gotten {required_roles_list}')
                logger.error(f'Unexpected roles gotten {required_roles_list}')

                return redirect('init_email_auth')

            user_role = getattr(request.user, 'role', None)
            if user_role not in required_roles_list:
                messages.error(request,
                               f'Register as a {str(required_roles_list)} to access this resource')
                logger.error(
                    f'Unexpected role gotten: {user_role} instead of {required_roles_list}')
                return redirect('init_email_auth')

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
