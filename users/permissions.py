"""
Permission mixins and decorators for role-based access control.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin


class AdminRequiredMixin(LoginRequiredMixin):
    """Mixin that requires the user to be an admin."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_admin:
            messages.error(request, 'Доступ только для администраторов.')
            return redirect('routes:list')
        return super().dispatch(request, *args, **kwargs)


class ManagerRequiredMixin(LoginRequiredMixin):
    """Mixin that requires the user to be a manager or admin."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_manager or request.user.is_admin):
            messages.error(request, 'Доступ только для менеджеров.')
            return redirect('routes:list')
        return super().dispatch(request, *args, **kwargs)


def admin_required(view_func):
    """Decorator for admin-only views."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin:
            messages.error(request, 'Доступ только для администраторов.')
            return redirect('routes:list')
        return view_func(request, *args, **kwargs)
    return wrapper


def manager_required(view_func):
    """Decorator for manager-or-admin views."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_manager or request.user.is_admin):
            messages.error(request, 'Доступ только для менеджеров.')
            return redirect('routes:list')
        return view_func(request, *args, **kwargs)
    return wrapper
