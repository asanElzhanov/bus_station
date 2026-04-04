from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('routes', '0001_initial'),
        ('transport', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('travel_date', models.DateField(verbose_name='Дата поездки')),
                ('price', models.DecimalField(
                    decimal_places=2, max_digits=10, verbose_name='Цена билета (тг)'
                )),
                ('customer_name', models.CharField(max_length=150, verbose_name='Имя клиента')),
                ('phone', models.CharField(max_length=20, verbose_name='Телефон')),
                ('extra_info', models.TextField(blank=True, verbose_name='Доп. информация')),
                ('status', models.CharField(
                    choices=[
                        ('booked', 'Забронировано'),
                        ('paid', 'Оплачено'),
                        ('cancelled', 'Отменено'),
                    ],
                    default='booked',
                    max_length=15,
                    verbose_name='Статус'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('route', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='bookings',
                    to='routes.route',
                    verbose_name='Маршрут'
                )),
                ('seat', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='bookings',
                    to='transport.seat',
                    verbose_name='Место'
                )),
                ('from_stop', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='bookings_from',
                    to='routes.stop',
                    verbose_name='Остановка посадки'
                )),
                ('to_stop', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='bookings_to',
                    to='routes.stop',
                    verbose_name='Остановка высадки'
                )),
            ],
            options={
                'verbose_name': 'Бронирование',
                'verbose_name_plural': 'Бронирования',
                'ordering': ['-created_at'],
            },
        ),
    ]
