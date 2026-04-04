"""
Payment model — mock payment system.
In production, replace the checkout view with real payment gateway (Kaspi, Stripe, etc.)
"""

from django.db import models


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает оплаты'
        SUCCESS = 'success', 'Оплачено'
        FAILED = 'failed', 'Ошибка'
        REFUNDED = 'refunded', 'Возврат'

    booking = models.OneToOneField(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='payment',
        verbose_name='Бронирование'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма')
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Статус'
    )
    # In real system: store transaction_id from payment gateway
    transaction_id = models.CharField(max_length=100, blank=True, verbose_name='ID транзакции')
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Платёж'
        verbose_name_plural = 'Платежи'

    def __str__(self):
        return f'Платёж #{self.pk} | {self.amount} тг | {self.get_status_display()}'
