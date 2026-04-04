from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # Публичные
    path('create/<int:route_pk>/seat/<int:seat_pk>/', views.BookingCreateView.as_view(), name='create'),
    path('confirm/<int:pk>/', views.BookingConfirmView.as_view(), name='confirm'),
    path('my/', views.MyBookingsView.as_view(), name='my'),
    path('refund/<uuid:token>/', views.GuestRefundView.as_view(), name='guest_refund'),

    # Менеджер
    path('', views.BookingListView.as_view(), name='list'),
    path('<int:pk>/', views.BookingDetailView.as_view(), name='detail'),
    path('<int:pk>/cancel/', views.BookingCancelView.as_view(), name='cancel'),
]
