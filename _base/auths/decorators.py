#!/usr/bin/env python3
"""Decorators for users views"""
from django.shortcuts import render
from functools import wraps


def role_required(required_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return render(request, 'error_pages/401.html', status=401)

            VALID_ROLES = {'CUSTOMER', 'RIDER', 'BUSINESS'}

            # Normalize required_roles to a list
            if isinstance(required_roles, str):
                required_roles_list = [required_roles]
            elif isinstance(required_roles, list):
                required_roles_list = required_roles
            else:
                return render(request, 'error_pages/400.html', status=400)

            # Validate required_roles
            if not all(role in VALID_ROLES for role in required_roles_list):
                return render(request, 'error_pages/400.html', status=400)

            user_role = getattr(request.user, 'role', None)
            if user_role not in required_roles_list:
                return render(request, 'error_pages/403.html', status=403)

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
