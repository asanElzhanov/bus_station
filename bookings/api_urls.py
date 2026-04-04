from django.urls import path
from .api_views import BookingSeatStatusAPIView

app_name = 'bookings-api'

urlpatterns = [
    path(
        'seats/<int:route_pk>/<int:from_stop_pk>/<int:to_stop_pk>/<str:travel_date>/',
        BookingSeatStatusAPIView.as_view(),
        name='seat-status'
    ),
]
