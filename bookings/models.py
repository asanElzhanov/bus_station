"""
Booking model.

Новое:
    - cookie_token  — UUID привязывающий бронь к браузеру гостя (7 дней)
    - user          — привязка брони к аккаунту для авторизованных пользователей
    - can_refund()  — можно вернуть до момента отправления с первой остановки
"""

import uuid
from django.conf import settings
from django.db import models


class Booking(models.Model):
    class Status(models.TextChoices):
        BOOKED    = 'booked',    'Забронировано'
        PAID      = 'paid',      'Оплачено'
        CANCELLED = 'cancelled', 'Отменено'
        REFUNDED  = 'refunded',  'Возвращён'

    route = models.ForeignKey(
        'routes.Route', on_delete=models.CASCADE,
        related_name='bookings', verbose_name='Маршрут'
    )
    seat = models.ForeignKey(
        'transport.Seat', on_delete=models.CASCADE,
        related_name='bookings', verbose_name='Место'
    )
    from_stop = models.ForeignKey(
        'routes.Stop', on_delete=models.CASCADE,
        related_name='bookings_from', verbose_name='Остановка посадки'
    )
    to_stop = models.ForeignKey(
        'routes.Stop', on_delete=models.CASCADE,
        related_name='bookings_to', verbose_name='Остановка высадки'
    )

    travel_date = models.DateField(verbose_name='Дата поездки')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена билета (тг)')

    customer_name = models.CharField(max_length=150, verbose_name='Имя клиента')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    extra_info = models.TextField(blank=True, verbose_name='Доп. информация')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='bookings',
        verbose_name='Пользователь',
    )

    status = models.CharField(
        max_length=15, choices=Status.choices,
        default=Status.BOOKED, verbose_name='Статус'
    )

    # ── Куки-токен для гостей ──────────────────────────────────────────────────
    # Генерируется при создании брони, сохраняется в куки на 7 дней.
    # По нему гость видит свои билеты без авторизации.
    cookie_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        verbose_name='Токен куки',
        help_text='Идентификатор браузера гостя'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-created_at']

    def __str__(self):
        return (
            f'Бронь #{self.pk} | '
            f'{self.from_stop.city}→{self.to_stop.city} | '
            f'{self.travel_date} | Место {self.seat.seat_number}'
        )

    @property
    def is_active(self):
        return self.status in (self.Status.BOOKED, self.Status.PAID)

    def can_refund(self):
        """
        Возврат возможен если:
          1. Статус paid или booked
          2. Текущее время < datetime отправления с первой остановки
        """
        import datetime
        if self.status not in (self.Status.BOOKED, self.Status.PAID):
            return False
        departure_dt = self.route.departure_datetime(self.travel_date)
        now = datetime.datetime.now()
        return now < departure_dt

    def refund_deadline(self):
        """Возвращает datetime дедлайна возврата."""
        return self.route.departure_datetime(self.travel_date)
