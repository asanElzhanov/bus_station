from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('transport', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Route',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(
                    help_text='Например: Астана — Алматы',
                    max_length=200,
                    verbose_name='Название маршрута'
                )),
                ('departure_time', models.TimeField(
                    verbose_name='Время отправления (с первой остановки)'
                )),
                ('is_approved', models.BooleanField(default=False, verbose_name='Подтверждён')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('transport', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='routes',
                    to='transport.transport',
                    verbose_name='Транспорт'
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='routes',
                    to='users.user',
                    verbose_name='Создан менеджером'
                )),
            ],
            options={
                'verbose_name': 'Маршрут',
                'verbose_name_plural': 'Маршруты',
                'ordering': ['name', 'departure_time'],
            },
        ),
        migrations.CreateModel(
            name='Stop',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('city', models.CharField(max_length=100, verbose_name='Город')),
                ('order', models.PositiveSmallIntegerField(verbose_name='Порядок (0, 1, 2 ...)')),
                ('price_from_start', models.DecimalField(
                    decimal_places=2,
                    default=0,
                    help_text='0 для первой остановки',
                    max_digits=10,
                    verbose_name='Цена от начала (тг)'
                )),
                ('arrival_offset_minutes', models.PositiveIntegerField(
                    default=0,
                    verbose_name='Смещение прибытия (мин от старта)'
                )),
                ('route', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='stops',
                    to='routes.route',
                    verbose_name='Маршрут'
                )),
            ],
            options={
                'verbose_name': 'Остановка',
                'verbose_name_plural': 'Остановки',
                'ordering': ['route', 'order'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='stop',
            unique_together={('route', 'order')},
        ),
    ]
