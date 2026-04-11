"""
Root views for config app.
"""

from django.shortcuts import redirect


def root_redirect(request):
    """
    Redirect root URL based on user role:
    - Manager/Admin -> bookings list
    - Others → public routes list
    """
    if request.user.is_authenticated and (request.user.is_manager or request.user.is_admin):
        return redirect('bookings:list')
    return redirect('routes:list')
