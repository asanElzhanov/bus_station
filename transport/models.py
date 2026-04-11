"""
Transport models: Vehicle and Seat.

Seat layout is stored as JSON in Transport.layout, for example:
[
  {"row": 1, "col": 1, "type": "window"},
  {"row": 1, "col": 2, "type": "aisle"},
  ...
]
Individual Seat objects are created from this layout via a signal/method.
"""

import json
from django.db import models


class Transport(models.Model):
    """
    Represents a vehicle (bus, minibus).
    Layout is a JSON array describing seat positions.
    """

    name = models.CharField(max_length=100, verbose_name='Название')
    total_seats = models.PositiveIntegerField(verbose_name='Количество мест')

    # JSON layout schema example:
    # [{"row":1,"col":1,"type":"window"},{"row":1,"col":2,"type":"aisle"}, ...]
    layout = models.JSONField(
        verbose_name='Схема сидений',
        help_text='JSON массив с позициями сидений: [{row, col, type, seat_number}]',
        default=list
    )

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='transports',
        verbose_name='Создан менеджером'
    )

    class Meta:
        verbose_name = 'Транспорт'
        verbose_name_plural = 'Транспорт'

    def __str__(self):
        return f'{self.name} ({self.total_seats} мест)'

    def generate_seats(self):
        """
        Create Seat objects based on the layout JSON.
        Called after saving a Transport instance.
        """
        self.seats.all().delete()
        seats_to_create = []
        for item in self.layout:
            if item.get('type') in ('passage', None):
                continue
            seats_to_create.append(Seat(
                transport=self,
                seat_number=item.get('seat_number', f'{item["row"]}{item["col"]}'),
                position_x=item.get('col', 1),
                position_y=item.get('row', 1),
                seat_type=item.get('type', Seat.SeatType.STANDARD),
            ))
        Seat.objects.bulk_create(seats_to_create)

    @staticmethod
    def default_layout(rows: int, cols: int) -> list:
        """
        Helper: generate a standard rectangular layout.
        Usage: Transport.default_layout(rows=8, cols=4)
        """
        layout = []
        num = 1
        for row in range(1, rows + 1):
            for col in range(1, cols + 1):
                seat_type = 'window' if col in (1, cols) else 'aisle'
                layout.append({
                    'seat_number': str(num),
                    'row': row,
                    'col': col,
                    'type': seat_type,
                })
                num += 1
        return layout


class Seat(models.Model):
    """Represents a physical seat in a transport vehicle."""

    class SeatType(models.TextChoices):
        WINDOW = 'window', 'У окна'
        AISLE = 'aisle', 'У прохода'
        STANDARD = 'standard', 'Стандартное'

    transport = models.ForeignKey(
        Transport,
        on_delete=models.CASCADE,
        related_name='seats',
        verbose_name='Транспорт'
    )
    seat_number = models.CharField(max_length=10, verbose_name='Номер места')
    position_x = models.PositiveIntegerField(verbose_name='Колонка (X)')
    position_y = models.PositiveIntegerField(verbose_name='Ряд (Y)')
    seat_type = models.CharField(
        max_length=20,
        choices=SeatType.choices,
        default=SeatType.STANDARD,
        verbose_name='Тип места'
    )

    class Meta:
        verbose_name = 'Место'
        verbose_name_plural = 'Места'
        unique_together = ('transport', 'seat_number')
        ordering = ['position_y', 'position_x']

    def __str__(self):
        return f'Место {self.seat_number} ({self.transport.name})'
