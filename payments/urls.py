from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('checkout/<int:booking_pk>/', views.CheckoutView.as_view(), name='checkout'),
    path('process/<int:booking_pk>/', views.PaymentProcessView.as_view(), name='process'),
]
