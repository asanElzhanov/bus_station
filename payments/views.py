"""
Mock payment views.
После успешной оплаты cookie_token брони добавляется в куки только для гостей.
"""

import uuid
from datetime import datetime, timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.views import View

from bookings.models import Booking
from bookings.cookie_utils import get_guest_tokens, add_guest_token
from .models import Payment


class CheckoutView(View):
    def get(self, request, booking_pk):
        booking = get_object_or_404(Booking, pk=booking_pk, status=Booking.Status.BOOKED)
        payment, _ = Payment.objects.get_or_create(
            booking=booking,
            defaults={'amount': booking.price, 'status': Payment.Status.PENDING}
        )
        return render(request, 'payments/checkout.html', {
            'booking': booking,
            'payment': payment,
        })


class PaymentProcessView(View):
    def post(self, request, booking_pk):
        booking = get_object_or_404(Booking, pk=booking_pk, status=Booking.Status.BOOKED)
        action  = request.POST.get('action')

        with transaction.atomic():
            payment, _ = Payment.objects.get_or_create(
                booking=booking,
                defaults={'amount': booking.price}
            )

            if action == 'pay':
                payment.status         = Payment.Status.SUCCESS
                payment.transaction_id = str(uuid.uuid4())[:16].upper()
                payment.paid_at        = datetime.now(tz=timezone.utc)
                payment.save()

                booking.status = Booking.Status.PAID
                booking.save()

                messages.success(
                    request,
                    f'✅ Оплата прошла! Транзакция: {payment.transaction_id}'
                )
                resp   = redirect('bookings:confirm', pk=booking.pk)
                if not request.user.is_authenticated:
                    # ── Записываем cookie_token в куки на 7 дней для гостей ──
                    tokens = get_guest_tokens(request)
                    add_guest_token(resp, tokens, str(booking.cookie_token))
                return resp

            elif action == 'cancel':
                payment.status = Payment.Status.FAILED
                payment.save()
                booking.status = Booking.Status.CANCELLED
                booking.save()
                messages.warning(request, 'Оплата отменена. Бронирование аннулировано.')
                return redirect('routes:list')

        return redirect('payments:checkout', booking_pk=booking_pk)
