"""
Booking views.

Новое:
    - При создании брони cookie_token пишется в куки (7 дней).
  - MyBookingsView — публичная страница «Мои билеты» по куки.
  - GuestRefundView — возврат билета гостем (до отправления).
  - Проверка is_boarding_allowed / is_alighting_allowed при создании брони.
"""

from datetime import date, datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.views import View
from django.utils import timezone

from users.permissions import ManagerRequiredMixin
from routes.models import Route, Stop
from transport.models import Seat
from .models import Booking
from .forms import BookingForm
from .cookie_utils import get_guest_tokens, add_guest_token, refresh_guest_tokens


# ─── Утилиты занятости ────────────────────────────────────────────────────────

def get_conflicting_bookings(route, seat, travel_date, from_order, to_order):
    return Booking.objects.filter(
        route=route, seat=seat, travel_date=travel_date,
        status__in=[Booking.Status.BOOKED, Booking.Status.PAID],
        from_stop__order__lt=to_order,
        to_stop__order__gt=from_order,
    )


def get_occupied_seat_ids(route, travel_date, from_stop, to_stop):
    return set(
        Booking.objects.filter(
            route=route, travel_date=travel_date,
            status__in=[Booking.Status.BOOKED, Booking.Status.PAID],
            from_stop__order__lt=to_stop.order,
            to_stop__order__gt=from_stop.order,
        ).values_list('seat_id', flat=True)
    )


def is_boarding_time_passed(travel_date, from_stop):
    """
    Returns True when boarding time at selected stop is already in the past.

    Rule:
      selected travel date + stop arrival time < current local datetime
    If arrival time is missing, fallback to departure time.
    """
    stop_time = from_stop.arrival_time or from_stop.departure_time
    if not stop_time:
        return False

    stop_datetime = datetime.combine(travel_date, stop_time)
    local_tz = timezone.get_current_timezone()
    stop_datetime = timezone.make_aware(stop_datetime, local_tz)
    return stop_datetime < timezone.localtime()


# ─── Публичные views ──────────────────────────────────────────────────────────

class BookingCreateView(View):
    """POST из модального окна. Проверяет ограничения остановок."""

    def post(self, request, route_pk, seat_pk):
        route = get_object_or_404(Route, pk=route_pk, is_approved=True)
        seat  = get_object_or_404(Seat, pk=seat_pk, transport=route.transport)
        form  = BookingForm(request.POST, route=route)

        if not form.is_valid():
            messages.error(request, 'Проверьте данные формы: ' + str(form.errors))
            return redirect(f'/routes/{route_pk}/')

        from_stop   = form.cleaned_data['from_stop']
        to_stop     = form.cleaned_data['to_stop']
        travel_date = form.cleaned_data['travel_date']

        max_booking_date = date.today() + timedelta(days=route.booking_max_days or 7)
        if travel_date > max_booking_date:
            messages.error(
                request,
                f'Билеты на этот маршрут можно купить только до {max_booking_date.strftime("%d.%m.%Y")}.'
            )
            return redirect(f'/routes/{route_pk}/?date={travel_date}&from_stop={from_stop.pk}&to_stop={to_stop.pk}')

        # ── Проверка ограничений остановок ───────────────────────────────────
        if not from_stop.is_boarding_allowed:
            messages.error(request, f'Посадка в «{from_stop.city}» недоступна для продажи.')
            return redirect(f'/routes/{route_pk}/?date={travel_date}&from_stop={from_stop.pk}&to_stop={to_stop.pk}')
        if not to_stop.is_alighting_allowed:
            messages.error(request, f'Высадка в «{to_stop.city}» недоступна для продажи.')
            return redirect(f'/routes/{route_pk}/?date={travel_date}&from_stop={from_stop.pk}&to_stop={to_stop.pk}')
        if is_boarding_time_passed(travel_date, from_stop):
            messages.error(
                request,
                f'Покупка с остановки «{from_stop.city}» недоступна: время прибытия уже прошло.'
            )
            return redirect(f'/routes/{route_pk}/?date={travel_date}&from_stop={from_stop.pk}&to_stop={to_stop.pk}')

        price = route.segment_price(from_stop, to_stop)

        try:
            with transaction.atomic():
                conflict = get_conflicting_bookings(
                    route, seat, travel_date,
                    from_stop.order, to_stop.order
                ).select_for_update().exists()

                if conflict:
                    raise IntegrityError('Место занято')

                booking = Booking.objects.create(
                    route=route, seat=seat,
                    from_stop=from_stop, to_stop=to_stop,
                    travel_date=travel_date, price=price,
                    customer_name=form.cleaned_data['customer_name'],
                    phone=form.cleaned_data['phone'],
                    extra_info=form.cleaned_data.get('extra_info', ''),
                    status=Booking.Status.BOOKED,
                )
        except IntegrityError:
            messages.error(
                request,
                f'Место №{seat.seat_number} уже занято на '
                f'{from_stop.city}→{to_stop.city} на {travel_date}.'
            )
            return redirect(
                f'/routes/{route_pk}/?date={travel_date}'
                f'&from_stop={from_stop.pk}&to_stop={to_stop.pk}'
            )

        messages.success(request, f'Билет успешно забронирован. Номер брони: #{booking.pk}.')
        resp = redirect('bookings:confirm', pk=booking.pk)
        tokens = get_guest_tokens(request)
        add_guest_token(resp, tokens, str(booking.cookie_token))
        return resp


class BookingConfirmView(View):
    """Страница подтверждения брони."""

    def get(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        tokens  = get_guest_tokens(request)
        resp    = render(request, 'bookings/confirm.html', {'booking': booking})
        # Обновляем TTL куки при каждом просмотре подтверждения
        refresh_guest_tokens(resp, tokens)
        return resp


# ─── «Мои билеты» (публичная страница по куки) ───────────────────────────────

class MyBookingsView(View):
    """
    Публичная страница — показывает все брони из куки браузера.
    Не требует авторизации.
    TTL куки сбрасывается на 7 дней при каждом посещении.
    """

    def get(self, request):
        tokens   = get_guest_tokens(request)
        bookings = []
        if tokens:
            bookings = list(
                Booking.objects.filter(cookie_token__in=tokens)
                .select_related('route', 'seat', 'from_stop', 'to_stop')
                .order_by('-created_at')
            )
        now = datetime.now()
        resp = render(request, 'bookings/my_bookings.html', {
            'bookings': bookings,
            'now': now,
        })
        # Сброс TTL на 7 дней при каждом посещении
        refresh_guest_tokens(resp, tokens)
        return resp


# ─── Возврат билета гостем ────────────────────────────────────────────────────

class GuestRefundView(View):
    """
    Гость возвращает свой билет.
    Проверяем:
      1. Токен в куки браузера совпадает с cookie_token брони.
      2. Текущее время < время отправления первой остановки.
    """

    def get(self, request, token):
        booking = get_object_or_404(Booking, cookie_token=token)
        tokens  = get_guest_tokens(request)
        if str(booking.cookie_token) not in tokens:
            messages.error(request, 'Билет не найден в вашем браузере.')
            return redirect('bookings:my')
        return render(request, 'bookings/refund_confirm.html', {'booking': booking})

    def post(self, request, token):
        booking = get_object_or_404(Booking, cookie_token=token)
        tokens  = get_guest_tokens(request)

        if str(booking.cookie_token) not in tokens:
            messages.error(request, 'Нет прав на возврат этого билета.')
            return redirect('bookings:my')

        if not booking.can_refund():
            messages.error(
                request,
                f'Возврат невозможен: маршрут уже отправился '
                f'({booking.route.departure_time.strftime("%H:%M")} '
                f'{booking.travel_date.strftime("%d.%m.%Y")}).'
            )
            return redirect('bookings:my')

        booking.status = Booking.Status.REFUNDED
        booking.save()
        messages.success(
            request,
            f'Билет #{booking.pk} успешно возвращён. '
            f'Средства будут зачислены в течение 3-5 рабочих дней.'
        )
        resp = redirect('bookings:my')
        return resp


# ─── Manager views ────────────────────────────────────────────────────────────

class BookingListView(ManagerRequiredMixin, View):
    def get(self, request):
        bookings = Booking.objects.select_related(
            'route', 'seat', 'from_stop', 'to_stop'
        ).order_by('-created_at')

        if not request.user.is_admin:
            bookings = bookings.filter(route__created_by=request.user)

        filter_date = request.GET.get('date', '').strip()
        filter_status = request.GET.get('status', '')

        # По умолчанию показываем сегодняшние брони, если дата не передана.
        if not filter_date:
            filter_date = str(date.today())

        try:
            bookings = bookings.filter(travel_date=date.fromisoformat(filter_date))
        except ValueError:
            filter_date = str(date.today())
            bookings = bookings.filter(travel_date=date.fromisoformat(filter_date))

        if filter_status in dict(Booking.Status.choices):
            bookings = bookings.filter(status=filter_status)

        return render(request, 'bookings/list.html', {
            'bookings': bookings,
            'filter_date': filter_date,
            'filter_status': filter_status,
            'status_choices': Booking.Status.choices,
        })


class BookingDetailView(ManagerRequiredMixin, View):
    def get(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        if not request.user.is_admin and booking.route.created_by != request.user:
            messages.error(request, 'Нет доступа.')
            return redirect('bookings:list')
        return render(request, 'bookings/detail.html', {'booking': booking})


class BookingCancelView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        if not request.user.is_admin and booking.route.created_by != request.user:
            messages.error(request, 'Нет доступа.')
            return redirect('bookings:list')
        booking.status = Booking.Status.CANCELLED
        booking.save()
        messages.success(request, f'Бронь #{booking.pk} отменена.')
        return redirect('bookings:list')
