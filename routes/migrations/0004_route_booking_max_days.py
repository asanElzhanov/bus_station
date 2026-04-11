from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('routes', '0003_stop_arrival_departure_times'),
    ]

    operations = [
        migrations.AddField(
            model_name='route',
            name='booking_max_days',
            field=models.PositiveSmallIntegerField(default=7, help_text='Сколько дней вперёд можно покупать билеты на этот маршрут', verbose_name='Максимум дней для продажи'),
        ),
    ]
