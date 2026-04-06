"""
Route + Stop models.

Stop.is_boarding_allowed  — можно ли СЕСТЬ на этой остановке
Stop.is_alighting_allowed — можно ли ВЫЙТИ на этой остановке

Пример: промежуточная «технологическая» остановка может быть
  is_boarding_allowed=False, is_alighting_allowed=False
  — автобус просто проезжает мимо, билеты туда/оттуда не продаются.
"""

from django.db import models


class Route(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название маршрута',
                            help_text='Например: Астана — Алматы')
    transport = models.ForeignKey(
        'transport.Transport', on_delete=models.PROTECT,
        related_name='routes', verbose_name='Транспорт'
    )
    departure_time = models.TimeField(verbose_name='Время отправления (с первой остановки)')
    is_approved = models.BooleanField(default=False, verbose_name='Подтверждён')
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True,
        related_name='routes', verbose_name='Создан менеджером'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Маршрут'
        verbose_name_plural = 'Маршруты'
        ordering = ['name', 'departure_time']

    def __str__(self):
        stops = list(self.stops.order_by('order'))
        if len(stops) >= 2:
            return f'{stops[0].city} → {stops[-1].city} ({self.departure_time:%H:%M})'
        return self.name

    @property
    def first_stop(self):
        return self.stops.order_by('order').first()

    @property
    def last_stop(self):
        return self.stops.order_by('order').last()

    @property
    def from_city(self):
        first = self.first_stop
        return first.city if first else ''

    @property
    def to_city(self):
        last = self.last_stop
        return last.city if last else ''

    @property
    def price(self):
        first = self.first_stop
        last = self.last_stop
        if not first or not last:
            return 0
        return self.segment_price(first, last)

    def segment_price(self, from_stop, to_stop):
        """Цена сегмента = разница цен от начала маршрута."""
        return max(0, float(to_stop.price_from_start) - float(from_stop.price_from_start))

    def departure_datetime(self, travel_date):
        """
        Возвращает datetime отправления с первой остановки для данной даты.
        Используется для проверки: можно ли ещё вернуть билет.
        """
        import datetime
        return datetime.datetime.combine(travel_date, self.departure_time)


class Stop(models.Model):
    """Одна остановка на маршруте."""
    route = models.ForeignKey(
        Route, on_delete=models.CASCADE,
        related_name='stops', verbose_name='Маршрут'
    )
    city = models.CharField(max_length=100, verbose_name='Город')
    order = models.PositiveSmallIntegerField(verbose_name='Порядок (0, 1, 2 ...)')
    price_from_start = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Цена от начала (тг)',
        help_text='0 для первой остановки'
    )
    arrival_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Время прибытия',
        help_text='Можно оставить пустым ("-")'
    )
    departure_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Время отправления',
        help_text='Можно оставить пустым ("-")'
    )

    # ── Ограничения продажи билетов ──────────────────────────────────────────
    is_boarding_allowed = models.BooleanField(
        default=True,
        verbose_name='Посадка разрешена',
        help_text='Можно ли купить билет ОТ этой остановки'
    )
    is_alighting_allowed = models.BooleanField(
        default=True,
        verbose_name='Высадка разрешена',
        help_text='Можно ли купить билет ДО этой остановки'
    )

    class Meta:
        verbose_name = 'Остановка'
        verbose_name_plural = 'Остановки'
        ordering = ['route', 'order']
        unique_together = ('route', 'order')

    def __str__(self):
        flags = []
        if not self.is_boarding_allowed:
            flags.append('нет посадки')
        if not self.is_alighting_allowed:
            flags.append('нет высадки')
        suffix = f' [{", ".join(flags)}]' if flags else ''
        return f'{self.city} (#{self.order}, {self.price_from_start} тг){suffix}'
