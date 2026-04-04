"""
Root URL configuration for bus_station project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/routes/', permanent=False)),
    path('users/', include('users.urls', namespace='users')),
    path('routes/', include('routes.urls', namespace='routes')),
    path('transport/', include('transport.urls', namespace='transport')),
    path('bookings/', include('bookings.urls', namespace='bookings')),
    path('payments/', include('payments.urls', namespace='payments')),

    # API endpoints
    path('api/routes/', include('routes.api_urls', namespace='routes-api')),
    path('api/bookings/', include('bookings.api_urls', namespace='bookings-api')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
