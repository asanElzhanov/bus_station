from datetime import datetime, timedelta

from django.db import migrations, models


def forwards_fill_times(apps, schema_editor):
    Stop = apps.get_model('routes', 'Stop')

    for stop in Stop.objects.select_related('route').all():
        base_time = stop.route.departure_time
        if base_time is None:
            continue

        arrival_dt = datetime.combine(datetime(2000, 1, 1), base_time) + timedelta(
            minutes=stop.arrival_offset_minutes or 0
        )
        computed_time = arrival_dt.time().replace(second=0, microsecond=0)

        if stop.order == 0:
            stop.arrival_time = None
            stop.departure_time = computed_time
        else:
            stop.arrival_time = computed_time
            # Старые данные не содержали стоянку, поэтому по умолчанию одинаковое время.
            stop.departure_time = computed_time

        stop.save(update_fields=['arrival_time', 'departure_time'])


def backwards_fill_offsets(apps, schema_editor):
    Stop = apps.get_model('routes', 'Stop')

    for stop in Stop.objects.select_related('route').all():
        base_time = stop.route.departure_time
        source_time = stop.arrival_time or stop.departure_time
        if base_time is None or source_time is None:
            stop.arrival_offset_minutes = 0
            stop.save(update_fields=['arrival_offset_minutes'])
            continue

        base_dt = datetime.combine(datetime(2000, 1, 1), base_time)
        source_dt = datetime.combine(datetime(2000, 1, 1), source_time)
        diff = int((source_dt - base_dt).total_seconds() // 60)
        stop.arrival_offset_minutes = max(diff, 0)
        stop.save(update_fields=['arrival_offset_minutes'])


class Migration(migrations.Migration):

    dependencies = [
        ('routes', '0002_stop_boarding_alighting'),
    ]

    operations = [
        migrations.AddField(
            model_name='stop',
            name='arrival_time',
            field=models.TimeField(
                blank=True,
                help_text='Можно оставить пустым ("-")',
                null=True,
                verbose_name='Время прибытия',
            ),
        ),
        migrations.AddField(
            model_name='stop',
            name='departure_time',
            field=models.TimeField(
                blank=True,
                help_text='Можно оставить пустым ("-")',
                null=True,
                verbose_name='Время отправления',
            ),
        ),
        migrations.RunPython(forwards_fill_times, backwards_fill_offsets),
        migrations.RemoveField(
            model_name='stop',
            name='arrival_offset_minutes',
        ),
    ]
