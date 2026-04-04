from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('bookings', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Сумма')),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Ожидает оплаты'),
                        ('success', 'Оплачено'),
                        ('failed', 'Ошибка'),
                        ('refunded', 'Возврат'),
                    ],
                    default='pending',
                    max_length=15,
                    verbose_name='Статус'
                )),
                ('transaction_id', models.CharField(
                    blank=True, max_length=100, verbose_name='ID транзакции'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('paid_at', models.DateTimeField(null=True, blank=True)),
                ('booking', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='payment',
                    to='bookings.booking',
                    verbose_name='Бронирование'
                )),
            ],
            options={
                'verbose_name': 'Платёж',
                'verbose_name_plural': 'Платежи',
            },
        ),
    ]
